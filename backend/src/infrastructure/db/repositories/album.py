import uuid
from collections import Counter
from datetime import date
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import String as SAString, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.repositories.album import AlbumRepository
from src.domain.entities.music import (
    Album,
    AlbumArchive,
    AlbumChangelog,
    AlbumCover,
    ArchiveLink,
    Artist,
    Disc,
    ExternalLink,
    Track,
)
from src.domain.value_objects.aliases import normalize_aliases
from src.infrastructure.db.models.music import (
    AlbumArchiveModel,
    AlbumChangelogModel,
    AlbumCoverModel,
    AlbumModel,
    ArchiveLinkModel,
    ArtistModel,
    DiscModel,
    EventModel,
    ExternalLinkModel,
    FranchiseModel,
    TrackArtistModel,
    TrackModel,
)
from src.infrastructure.storage.object_storage import MinioObjectStorageService


class SqlAlchemyAlbumRepository(AlbumRepository):
    def __init__(self, session: AsyncSession, redis: Redis | None = None) -> None:
        self._session = session
        self._redis = redis

    @staticmethod
    def _format_date(year: int | None, month: int | None, day: int | None) -> str:
        if not year:
            return ""
        m = f"{month:02d}" if month else "01"
        d = f"{day:02d}" if day else "01"
        return f"{year}.{m}.{d}"

    @staticmethod
    def _change_entry(old_str: str, new_str: str) -> dict[str, Any]:
        if not old_str and new_str:
            return {"type": "added", "new": new_str}
        if old_str and not new_str:
            return {"type": "removed", "old": old_str}
        return {"type": "updated", "old": old_str, "new": new_str}

    @staticmethod
    def _as_str(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "Yes" if value else "No"
        return str(value).strip()

    @classmethod
    def _check_field(
        cls, diff: dict[str, dict[str, Any]], label: str, old_val: Any, new_val: Any
    ) -> None:
        old_str, new_str = cls._as_str(old_val), cls._as_str(new_val)
        if old_str != new_str:
            diff[label] = cls._change_entry(old_str, new_str)

    @staticmethod
    def _fmt_aliases(aliases: list[str] | None) -> str:
        return ", ".join(aliases) if aliases else ""

    @staticmethod
    def _fmt_duration(seconds: int | None) -> str:
        if seconds is None:
            return ""
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    @staticmethod
    def _fmt_blob(text: str | None) -> str:
        return f"{len(text):,} chars" if text else ""

    @staticmethod
    def _fmt_bitrate(kbps: int | None, mode: Any) -> str:
        if kbps is None:
            return ""
        mode_str = f" {mode}" if mode else ""
        return f"{kbps} kbps{mode_str}"

    def _diff_scalar_fields(self, model: AlbumModel, new_album: Album) -> dict[str, dict[str, Any]]:
        diff: dict[str, dict[str, Any]] = {}
        self._check_field(diff, "Title (Original)", model.title_original, new_album.title_original)
        self._check_field(
            diff, "Aliases", self._fmt_aliases(model.aliases), self._fmt_aliases(new_album.aliases)
        )
        self._check_field(diff, "Label", model.label, new_album.label)
        self._check_field(diff, "Publisher", model.publisher, new_album.publisher)
        self._check_field(diff, "Storage Drive", model.storage_drive, new_album.storage_drive)
        self._check_field(diff, "Relative Path", model.relative_path, new_album.relative_path)
        self._check_field(
            diff, "Folder Name", model.original_folder_name, new_album.original_folder_name
        )
        old_date = self._format_date(model.release_year, model.release_month, model.release_day)
        new_date = self._format_date(
            new_album.release_year, new_album.release_month, new_album.release_day
        )
        self._check_field(diff, "Release Date", old_date, new_date)
        return diff

    def _diff_album_artist(
        self, model: AlbumModel, new_artist_id: uuid.UUID | None, new_artist_name: str | None
    ) -> dict[str, dict[str, Any]]:
        diff: dict[str, dict[str, Any]] = {}
        if new_artist_id == model.album_artist_id:
            return diff
        old_name = model.album_artist.name_original if model.album_artist else ""
        new_name = new_artist_name or (str(new_artist_id) if new_artist_id else "")
        self._check_field(diff, "Album Artist", old_name, new_name)
        return diff

    def _diff_disc_fields(self, model: AlbumModel, new_album: Album) -> dict[str, dict[str, Any]]:
        diff: dict[str, dict[str, Any]] = {}
        old_discs = {d.disc_number: d for d in model.discs}
        new_discs = {d.disc_number: d for d in new_album.discs}
        for n in sorted(set(old_discs) | set(new_discs)):
            if n not in old_discs:
                d = new_discs[n]
                diff[f"Disc {n}"] = self._change_entry(
                    "", f"{d.media_type}/{d.container_format}, {len(d.tracks)} track(s)"
                )
                continue
            if n not in new_discs:
                d = old_discs[n]
                diff[f"Disc {n}"] = self._change_entry(
                    f"{d.media_type}/{d.container_format}, {len(d.tracks)} track(s)", ""
                )
                continue
            old, new = old_discs[n], new_discs[n]
            prefix = f"Disc {n} · "
            self._check_field(diff, prefix + "Media Type", old.media_type, new.media_type)
            self._check_field(
                diff, prefix + "Container", old.container_format, new.container_format
            )
            self._check_field(
                diff, prefix + "Catalog Number", old.catalog_number, new.catalog_number
            )
            self._check_field(diff, prefix + "Log Type", old.log_type, new.log_type)
            self._check_field(diff, prefix + "Log Score", old.log_score, new.log_score)
            self._check_field(
                diff,
                prefix + "Ripper Log",
                self._fmt_blob(old.raw_log_text),
                self._fmt_blob(new.raw_log_text),
            )
            self._check_field(
                diff,
                prefix + "CUE Sheet",
                self._fmt_blob(old.raw_cue_text),
                self._fmt_blob(new.raw_cue_text),
            )
            self._check_field(
                diff,
                prefix + "AccurateRip",
                self._fmt_blob(old.accuraterip_summary),
                self._fmt_blob(new.accuraterip_summary),
            )
        return diff

    @staticmethod
    def _credits_summary_from_model(track: TrackModel) -> str:
        parts = sorted(
            f"{assoc.artist.name_original} ({assoc.role})" for assoc in track.artist_associations
        )
        return ", ".join(parts)

    @staticmethod
    def _credits_summary_from_entity(track: Track) -> str:
        parts = sorted(f"{a.name_original} ({a.role})" for a in track.artists)
        return ", ".join(parts)

    def _diff_track_matrix(self, model: AlbumModel, new_album: Album) -> dict[str, dict[str, Any]]:
        diff: dict[str, dict[str, Any]] = {}
        old_tracks = {(d.disc_number, t.track_number): t for d in model.discs for t in d.tracks}
        new_tracks = {(d.disc_number, t.track_number): t for d in new_album.discs for t in d.tracks}
        for key in sorted(set(old_tracks) | set(new_tracks)):
            disc_num, trk_num = key
            tag = f"D{disc_num}T{trk_num}"
            if key not in old_tracks:
                diff[tag] = self._change_entry("", new_tracks[key].title_original)
                continue
            if key not in new_tracks:
                diff[tag] = self._change_entry(old_tracks[key].title_original, "")
                continue
            old, new = old_tracks[key], new_tracks[key]
            prefix = f"{tag} · "
            self._check_field(diff, prefix + "Title", old.title_original, new.title_original)
            self._check_field(
                diff,
                prefix + "Aliases",
                self._fmt_aliases(old.aliases),
                self._fmt_aliases(new.aliases),
            )
            self._check_field(
                diff,
                prefix + "Duration",
                self._fmt_duration(old.duration_seconds),
                self._fmt_duration(new.duration_seconds),
            )
            self._check_field(diff, prefix + "Audio Codec", old.audio_codec, new.audio_codec)
            self._check_field(diff, prefix + "Video Codec", old.video_codec, new.video_codec)
            self._check_field(diff, prefix + "Bit Depth", old.bit_depth, new.bit_depth)
            self._check_field(diff, prefix + "Sample Rate", old.sample_rate, new.sample_rate)
            self._check_field(
                diff,
                prefix + "Bitrate",
                self._fmt_bitrate(old.bitrate_kbps, old.bitrate_mode),
                self._fmt_bitrate(new.bitrate_kbps, new.bitrate_mode),
            )
            self._check_field(
                diff, prefix + "Instrumental", old.is_instrumental, new.is_instrumental
            )
            self._check_field(
                diff,
                prefix + "Credits",
                self._credits_summary_from_model(old),
                self._credits_summary_from_entity(new),
            )
        return diff

    @staticmethod
    def _diff_external_links(model: AlbumModel, new_album: Album) -> dict[str, dict[str, Any]]:
        diff: dict[str, dict[str, Any]] = {}
        old_ext = {(el.site_name, el.url) for el in model.external_links}
        new_ext = {(el.site_name, el.url) for el in new_album.external_links}
        for site, url in new_ext - old_ext:
            diff[f"External Link (+{site})"] = {"type": "added", "new": url}
        for site, url in old_ext - new_ext:
            diff[f"External Link (-{site})"] = {"type": "removed", "old": url}
        return diff

    def _diff_archives_and_mirrors(
        self, model: AlbumModel, new_album: Album
    ) -> dict[str, dict[str, Any]]:
        diff: dict[str, dict[str, Any]] = {}
        old_archives = {a.archive_name: a for a in model.archives}
        new_archives = {a.archive_name: a for a in new_album.archives}
        for name in sorted(set(old_archives) | set(new_archives)):
            if name not in old_archives:
                diff[f"Archive Volume (+{name})"] = {"type": "added", "new": name}
                continue
            if name not in new_archives:
                diff[f"Archive Volume (-{name})"] = {"type": "removed", "old": name}
                continue
            old, new = old_archives[name], new_archives[name]
            prefix = f"Archive {name} · "
            self._check_field(
                diff, prefix + "Password", old.encryption_password, new.encryption_password
            )
            self._check_field(diff, prefix + "File Size", old.file_size_bytes, new.file_size_bytes)
            self._check_field(diff, prefix + "SHA-256", old.hash_sha256, new.hash_sha256)
        old_links = {
            f"{a.archive_name} [{link.provider_name}]": link.download_url
            for a in model.archives
            for link in a.links
        }
        new_links = {
            f"{a.archive_name} [{link.provider_name}]": link.download_url
            for a in new_album.archives
            for link in a.links
        }
        for key in sorted(set(old_links) | set(new_links)):
            if key not in old_links:
                diff[f"Archive Mirror (+{key})"] = {"type": "added", "new": new_links[key]}
            elif key not in new_links:
                diff[f"Archive Mirror (-{key})"] = {"type": "removed", "old": old_links[key]}
            elif old_links[key] != new_links[key]:
                diff[f"Archive Mirror ({key})"] = {
                    "type": "updated",
                    "old": old_links[key],
                    "new": new_links[key],
                }
        return diff

    def _diff_covers(self, model: AlbumModel, new_album: Album) -> dict[str, dict[str, Any]]:
        diff: dict[str, dict[str, Any]] = {}

        def summarize(types: list[str]) -> str:
            counts = Counter(t or "Other" for t in types)
            return ", ".join(f"{t} ×{n}" for t, n in sorted(counts.items()))

        old_summary = summarize([c.cover_type for c in model.covers])
        new_summary = summarize([c.cover_type for c in new_album.covers])
        self._check_field(diff, "Cover Scans", old_summary, new_summary)
        return diff

    def _compute_album_diff(
        self,
        model: AlbumModel,
        new_album: Album,
        new_artist_id: uuid.UUID | None = None,
        new_artist_name: str | None = None,
    ) -> dict[str, dict[str, Any]]:
        diff = self._diff_scalar_fields(model, new_album)
        diff.update(self._diff_album_artist(model, new_artist_id, new_artist_name))
        diff.update(self._diff_disc_fields(model, new_album))
        diff.update(self._diff_track_matrix(model, new_album))
        diff.update(self._diff_external_links(model, new_album))
        diff.update(self._diff_archives_and_mirrors(model, new_album))
        diff.update(self._diff_covers(model, new_album))
        if not diff:
            diff["Metadata Sync"] = {"type": "updated", "old": "Identical", "new": "Re-saved"}
        return diff

    @staticmethod
    def _compute_sort_date(year: int | None, month: int | None, day: int | None) -> date | None:
        if not year:
            return None
        m = month if (month and 1 <= month <= 12) else 1
        d = day if (day and 1 <= day <= 31) else 1
        try:
            return date(year, m, d)
        except ValueError:
            return date(year, m, 1)

    async def _invalidate_album_cache(self, album_id: uuid.UUID) -> None:
        if not self._redis:
            return
        await self._redis.delete(f"album:cache:{album_id}")
        keys = [k async for k in self._redis.scan_iter("album:search:*")]
        if keys:
            await self._redis.delete(*keys)

    async def _resolve_album_artist_id(
        self, album: Album, album_artist_aliases: list[str] | None = None
    ) -> uuid.UUID | None:
        artist_id = album.album_artist_id
        if artist_id:
            check_stmt = select(ArtistModel.id).where(ArtistModel.id == artist_id)
            res = await self._session.execute(check_stmt)
            if not res.scalar_one_or_none():
                artist_id = None

        if not artist_id and album.album_artist and album.album_artist.name_original:
            name_orig = album.album_artist.name_original.strip()

            try:
                artist_uuid = uuid.UUID(name_orig)
                stmt = select(ArtistModel).where(ArtistModel.id == artist_uuid)
            except ValueError:
                stmt = select(ArtistModel).where(ArtistModel.name_original.ilike(name_orig))

            res = await self._session.execute(stmt.limit(1))
            found = res.scalars().first()
            if found:
                artist_id = found.id
                incoming = album_artist_aliases or (
                    album.album_artist.aliases if album.album_artist else []
                )
                if incoming:
                    merged = list(found.aliases or [])
                    seen = {a.casefold() for a in merged}
                    for alias in incoming:
                        if alias.casefold() not in seen:
                            merged.append(alias)
                            seen.add(alias.casefold())
                    found.aliases = merged
            else:
                new_a = ArtistModel(
                    id=uuid.uuid4(),
                    name_original=name_orig,
                    aliases=normalize_aliases(
                        album_artist_aliases
                        or (album.album_artist.aliases if album.album_artist else [])
                    ),
                )
                self._session.add(new_a)
                artist_id = new_a.id
        return artist_id

    async def _resolve_event_id(self, raw_event_id: uuid.UUID | str | None) -> uuid.UUID | None:
        if not raw_event_id:
            return None

        event_uuid = None
        if isinstance(raw_event_id, uuid.UUID):
            event_uuid = raw_event_id
        elif isinstance(raw_event_id, str) and raw_event_id.strip():
            try:
                event_uuid = uuid.UUID(raw_event_id.strip())
            except ValueError:
                event_uuid = None

        if event_uuid:
            res = await self._session.execute(
                select(EventModel.id).where(EventModel.id == event_uuid)
            )
            if res.scalar_one_or_none():
                return event_uuid

        event_name = str(raw_event_id).strip()
        if not event_name:
            return None

        stmt = (
            select(EventModel)
            .where(
                or_(
                    EventModel.short_name.ilike(event_name),
                    EventModel.full_name.ilike(event_name),
                )
            )
            .limit(1)
        )
        res = await self._session.execute(stmt)
        found = res.scalars().first()
        if found:
            return found.id

        new_event = EventModel(
            id=uuid.uuid4(),
            short_name=event_name,
            full_name=None,
            status="HELD",
        )
        self._session.add(new_event)
        await self._session.flush()
        return new_event.id

    async def _resolve_franchise_id(
        self,
        raw_franchise_id: uuid.UUID | str | None,
        franchise_aliases: list[str] | None = None,
    ) -> uuid.UUID | None:
        if not raw_franchise_id and not franchise_aliases:
            return None

        franchise_uuid = None
        if isinstance(raw_franchise_id, uuid.UUID):
            franchise_uuid = raw_franchise_id
        elif isinstance(raw_franchise_id, str) and raw_franchise_id.strip():
            try:
                franchise_uuid = uuid.UUID(raw_franchise_id.strip())
            except ValueError:
                franchise_uuid = None

        if franchise_uuid:
            stmt = select(FranchiseModel).where(FranchiseModel.id == franchise_uuid)
            res = await self._session.execute(stmt)
            found = res.scalars().first()
            if found:
                if franchise_aliases:
                    merged = list(found.aliases or [])
                    seen = {a.casefold() for a in merged}
                    for alias in franchise_aliases:
                        if alias.casefold() not in seen:
                            merged.append(alias)
                            seen.add(alias.casefold())
                    found.aliases = merged
                return franchise_uuid

        candidate_name = None
        if isinstance(raw_franchise_id, str) and raw_franchise_id.strip():
            candidate_name = raw_franchise_id.strip()
        elif franchise_aliases and len(franchise_aliases) > 0:
            candidate_name = franchise_aliases[0].strip()

        if not candidate_name:
            return None

        stmt = (
            select(FranchiseModel)
            .where(
                or_(
                    FranchiseModel.name_original.ilike(candidate_name),
                    cast(FranchiseModel.aliases, SAString).ilike(f"%{candidate_name}%"),
                )
            )
            .limit(1)
        )
        res = await self._session.execute(stmt)
        found = res.scalars().first()
        if found:
            if franchise_aliases:
                merged = list(found.aliases or [])
                seen = {a.casefold() for a in merged}
                for alias in franchise_aliases:
                    if alias.casefold() not in seen:
                        merged.append(alias)
                        seen.add(alias.casefold())
                found.aliases = merged
            return found.id

        new_franchise = FranchiseModel(
            id=uuid.uuid4(),
            name_original=candidate_name,
            aliases=normalize_aliases(franchise_aliases),
            franchise_type="Game",
        )
        self._session.add(new_franchise)
        return new_franchise.id

    async def _process_track_artists(self, track_model: TrackModel, track: Track) -> None:
        for track_artist in track.artists:
            name_orig = track_artist.name_original.strip()

            try:
                artist_uuid = uuid.UUID(name_orig)
                stmt = select(ArtistModel).where(ArtistModel.id == artist_uuid)
            except ValueError:
                stmt = select(ArtistModel).where(ArtistModel.name_original.ilike(name_orig))

            res = await self._session.execute(stmt.limit(1))
            artist_m = res.scalars().first()
            if artist_m is None:
                artist_m = ArtistModel(
                    id=track_artist.id or uuid.uuid4(),
                    name_original=name_orig,
                    aliases=normalize_aliases(track_artist.aliases),
                )
                self._session.add(artist_m)
            elif track_artist.aliases:
                merged = list(artist_m.aliases or [])
                seen = {a.casefold() for a in merged}
                for alias in track_artist.aliases:
                    if alias.casefold() not in seen:
                        merged.append(alias)
                        seen.add(alias.casefold())
                artist_m.aliases = merged

            t_role = getattr(track_artist, "role", "Composer") or "Composer"
            track_model.artist_associations.append(
                TrackArtistModel(track_id=track.id, artist_id=artist_m.id, role=t_role)
            )

    async def _sync_discs(
        self, album_id: uuid.UUID, discs: list[Disc], album_model: AlbumModel
    ) -> None:
        for d in discs:
            disc_model = DiscModel(
                id=d.id,
                album_id=album_id,
                disc_number=d.disc_number,
                catalog_number=d.catalog_number,
                media_type=str(d.media_type),
                container_format=str(d.container_format),
                log_type=str(d.log_type) if d.log_type else None,
                log_score=d.log_score,
                raw_log_text=d.raw_log_text,
                raw_cue_text=d.raw_cue_text,
                accuraterip_summary=d.accuraterip_summary,
            )
            for t in d.tracks:
                track_model = TrackModel(
                    id=t.id,
                    disc_id=d.id,
                    track_number=t.track_number,
                    title_original=t.title_original,
                    aliases=t.aliases,
                    duration_seconds=t.duration_seconds,
                    audio_codec=str(t.audio_codec) if t.audio_codec else None,
                    video_codec=str(t.video_codec) if t.video_codec else None,
                    bit_depth=t.bit_depth,
                    sample_rate=t.sample_rate,
                    bitrate_kbps=t.bitrate_kbps,
                    bitrate_mode=str(t.bitrate_mode) if t.bitrate_mode else None,
                    is_instrumental=t.is_instrumental,
                )
                await self._process_track_artists(track_model, t)
                disc_model.tracks.append(track_model)
            album_model.discs.append(disc_model)

    @staticmethod
    def _sync_auxiliary_data(
        album: Album,
        album_model: AlbumModel,
        user_id: uuid.UUID | None,
        action: str,
        changes_payload: dict[str, Any],
    ) -> None:
        for c in album.covers:
            album_model.covers.append(
                AlbumCoverModel(
                    id=c.id,
                    album_id=album.id,
                    storage_path=c.storage_path,
                    thumbhash=c.thumbhash,
                    cover_type=c.cover_type,
                )
            )
        for arch in album.archives:
            arch_model = AlbumArchiveModel(
                id=arch.id,
                album_id=album.id,
                archive_name=arch.archive_name,
                encryption_password=arch.encryption_password,
                file_size_bytes=arch.file_size_bytes,
                hash_sha256=arch.hash_sha256,
            )
            for lnk in arch.links:
                arch_model.links.append(
                    ArchiveLinkModel(
                        id=lnk.id,
                        archive_id=arch.id,
                        provider_name=lnk.provider_name,
                        download_url=lnk.download_url,
                        is_active=lnk.is_active,
                    )
                )
            album_model.archives.append(arch_model)
        for el in album.external_links:
            album_model.external_links.append(
                ExternalLinkModel(
                    id=el.id,
                    album_id=el.album_id,
                    site_name=el.site_name,
                    url=el.url,
                )
            )
        album_model.changelogs.append(
            AlbumChangelogModel(
                id=uuid.uuid4(),
                album_id=album.id,
                user_id=user_id,
                action=action,
                changes=changes_payload,
            )
        )

    async def save(
        self,
        album: Album,
        user_id: uuid.UUID | None = None,
        album_artist_aliases: list[str] | None = None,
        franchise_aliases: list[str] | None = None,
    ) -> None:
        stmt = (
            select(AlbumModel)
            .where(AlbumModel.id == album.id)
            .options(
                selectinload(AlbumModel.covers),
                selectinload(AlbumModel.album_artist),
                selectinload(AlbumModel.discs)
                .selectinload(DiscModel.tracks)
                .selectinload(TrackModel.artist_associations)
                .joinedload(TrackArtistModel.artist),
                selectinload(AlbumModel.archives).selectinload(AlbumArchiveModel.links),
                selectinload(AlbumModel.external_links),
                selectinload(AlbumModel.changelogs),
            )
        )
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()

        artist_id = await self._resolve_album_artist_id(
            album, album_artist_aliases=album_artist_aliases
        )
        event_id = await self._resolve_event_id(album.event_id)
        franchise_id = await self._resolve_franchise_id(
            album.franchise_id, franchise_aliases=franchise_aliases
        )

        sort_date = self._compute_sort_date(
            album.release_year, album.release_month, album.release_day
        )

        if model is None:
            action = "INSERT"
            changes_payload = {
                "Album Created": {
                    "type": "added",
                    "new": f"Ingested '{album.title_original}' with {len(album.discs)} disc(s)",
                }
            }
            model = AlbumModel(
                id=album.id,
                title_original=album.title_original,
                aliases=album.aliases,
                release_year=album.release_year,
                release_month=album.release_month,
                release_day=album.release_day,
                release_date_sort=sort_date,
                label=album.label,
                publisher=album.publisher,
                event_id=event_id,
                franchise_id=franchise_id,
                album_artist_id=artist_id,
                storage_drive=album.storage_drive,
                relative_path=album.relative_path,
                original_folder_name=album.original_folder_name,
            )
            self._session.add(model)
        else:
            action = "UPDATE"
            new_artist_name: str | None = None
            if artist_id and artist_id != model.album_artist_id:
                name_res = await self._session.execute(
                    select(ArtistModel.name_original).where(ArtistModel.id == artist_id)
                )
                new_artist_name = name_res.scalar_one_or_none()
            changes_payload = self._compute_album_diff(
                model, album, new_artist_id=artist_id, new_artist_name=new_artist_name
            )
            model.title_original = album.title_original
            model.aliases = album.aliases
            model.release_year = album.release_year
            model.release_month = album.release_month
            model.release_day = album.release_day
            model.release_date_sort = sort_date
            model.label = album.label
            model.publisher = album.publisher
            model.event_id = event_id
            model.franchise_id = franchise_id
            model.album_artist_id = artist_id
            model.storage_drive = album.storage_drive
            model.relative_path = album.relative_path
            model.original_folder_name = album.original_folder_name
            model.discs.clear()
            model.covers.clear()
            model.archives.clear()
            model.external_links.clear()
            await self._session.flush()

        await self._sync_discs(album.id, album.discs, model)
        self._sync_auxiliary_data(album, model, user_id, action, changes_payload)
        await self._invalidate_album_cache(album.id)

    async def find_by_id(self, album_id: uuid.UUID) -> Album | None:
        stmt = (
            select(AlbumModel)
            .where(AlbumModel.id == album_id)
            .options(
                selectinload(AlbumModel.covers),
                selectinload(AlbumModel.album_artist),
                selectinload(AlbumModel.discs)
                .selectinload(DiscModel.tracks)
                .selectinload(TrackModel.artist_associations)
                .joinedload(TrackArtistModel.artist),
                selectinload(AlbumModel.archives).selectinload(AlbumArchiveModel.links),
                selectinload(AlbumModel.external_links),
                selectinload(AlbumModel.changelogs),
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_domain_entity(model)

    async def search(
        self,
        query: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Album], int]:
        base_stmt = select(AlbumModel)
        if query and query.strip():
            pattern = f"%{query.strip()}%"
            base_stmt = base_stmt.where(
                AlbumModel.title_original.ilike(pattern)
                | AlbumModel.original_folder_name.ilike(pattern)
                | cast(AlbumModel.aliases, SAString).ilike(pattern)
            )
        subq = base_stmt.subquery()
        count_stmt = select(func.count()).select_from(subq)
        total_count = (await self._session.execute(count_stmt)).scalar_one()
        fetch_stmt = (
            base_stmt.order_by(AlbumModel.release_date_sort.desc().nulls_last())
            .offset(offset)
            .limit(limit)
            .options(
                selectinload(AlbumModel.covers),
                selectinload(AlbumModel.album_artist),
                selectinload(AlbumModel.discs)
                .selectinload(DiscModel.tracks)
                .selectinload(TrackModel.artist_associations)
                .joinedload(TrackArtistModel.artist),
                selectinload(AlbumModel.archives).selectinload(AlbumArchiveModel.links),
                selectinload(AlbumModel.external_links),
                selectinload(AlbumModel.changelogs),
            )
        )
        result = await self._session.execute(fetch_stmt)
        return [self._to_domain_entity(m) for m in result.scalars().all()], total_count

    async def delete(self, album_id: uuid.UUID) -> bool:
        stmt = select(AlbumModel).where(AlbumModel.id == album_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return False
        await self._session.delete(model)
        await self._invalidate_album_cache(album_id)
        return True

    @staticmethod
    def _to_domain_entity(model: AlbumModel) -> Album:
        discs = []
        for d in model.discs:
            tracks = [
                Track(
                    id=t.id,
                    disc_id=t.disc_id,
                    track_number=t.track_number,
                    title_original=t.title_original,
                    aliases=list(t.aliases or []),
                    duration_seconds=t.duration_seconds,
                    audio_codec=t.audio_codec,
                    video_codec=t.video_codec,
                    bit_depth=t.bit_depth,
                    sample_rate=t.sample_rate,
                    bitrate_kbps=t.bitrate_kbps,
                    bitrate_mode=t.bitrate_mode,
                    is_instrumental=t.is_instrumental,
                    artists=[
                        Artist(
                            id=assoc.artist.id,
                            name_original=assoc.artist.name_original,
                            aliases=list(assoc.artist.aliases or []),
                            role=assoc.role,
                            created_at=assoc.artist.created_at,
                        )
                        for assoc in t.artist_associations
                    ],
                )
                for t in d.tracks
            ]
            tracks.sort(key=lambda x: x.track_number)
            discs.append(
                Disc(
                    id=d.id,
                    album_id=d.album_id,
                    disc_number=d.disc_number,
                    catalog_number=d.catalog_number,
                    media_type=d.media_type,
                    container_format=d.container_format,
                    log_type=d.log_type,
                    log_score=d.log_score,
                    raw_log_text=d.raw_log_text,
                    raw_cue_text=d.raw_cue_text,
                    accuraterip_summary=d.accuraterip_summary,
                    tracks=tracks,
                )
            )
        discs.sort(key=lambda x: x.disc_number)

        album_artist = None
        if model.album_artist:
            album_artist = Artist(
                id=model.album_artist.id,
                name_original=model.album_artist.name_original,
                aliases=list(model.album_artist.aliases or []),
                created_at=model.album_artist.created_at,
            )

        covers = [
            AlbumCover(
                id=c.id,
                album_id=c.album_id,
                storage_path=c.storage_path,
                thumbhash=c.thumbhash,
                url=MinioObjectStorageService.get_public_url(c.storage_path),
                cover_type=c.cover_type,
                created_at=c.created_at,
            )
            for c in model.covers
        ]

        archives = []
        for arch in model.archives:
            links = [
                ArchiveLink(
                    id=lnk.id,
                    archive_id=lnk.archive_id,
                    provider_name=lnk.provider_name,
                    download_url=lnk.download_url,
                    is_active=lnk.is_active,
                )
                for lnk in arch.links
            ]
            archives.append(
                AlbumArchive(
                    id=arch.id,
                    album_id=arch.album_id,
                    archive_name=arch.archive_name,
                    encryption_password=arch.encryption_password,
                    file_size_bytes=arch.file_size_bytes,
                    hash_sha256=arch.hash_sha256,
                    links=links,
                )
            )

        external_links = [
            ExternalLink(
                id=el.id,
                album_id=el.album_id,
                site_name=el.site_name,
                url=el.url,
            )
            for el in model.external_links
        ]

        changelogs = [
            AlbumChangelog(
                id=cl.id,
                album_id=cl.album_id,
                user_id=cl.user_id,
                action=cl.action,
                changes=cl.changes,
                created_at=cl.created_at,
            )
            for cl in model.changelogs
        ]

        return Album(
            id=model.id,
            title_original=model.title_original,
            aliases=list(model.aliases or []),
            release_year=model.release_year,
            release_month=model.release_month,
            release_day=model.release_day,
            release_date_sort=model.release_date_sort,
            label=model.label,
            publisher=model.publisher,
            event_id=model.event_id,
            franchise_id=model.franchise_id,
            album_artist_id=model.album_artist_id,
            album_artist=album_artist,
            storage_drive=model.storage_drive,
            relative_path=model.relative_path,
            original_folder_name=model.original_folder_name,
            created_at=model.created_at,
            updated_at=model.updated_at,
            discs=discs,
            covers=covers,
            archives=archives,
            external_links=external_links,
            changelogs=changelogs,
        )
