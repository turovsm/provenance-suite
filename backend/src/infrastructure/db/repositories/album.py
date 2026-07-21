import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.application.repositories.album import AlbumRepository
from src.domain.entities.music import (
    Album,
    AlbumArchive,
    AlbumCover,
    ArchiveLink,
    Artist,
    Disc,
    ExternalLink,
    Track,
)
from src.domain.value_objects.music_types import LibraryCategory
from src.infrastructure.db.models.music import (
    AlbumArchiveModel,
    AlbumArtistModel,
    AlbumCategoryModel,
    AlbumCoverModel,
    AlbumModel,
    ArchiveLinkModel,
    DiscModel,
    ExternalLinkModel,
    TrackModel,
)


class SqlAlchemyAlbumRepository(AlbumRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, album: Album) -> None:
        stmt = select(AlbumModel).where(AlbumModel.id == album.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            model = AlbumModel(
                id=album.id,
                title_original=album.title_original,
                title_translated=album.title_translated,
                release_date=album.release_date,
                label=album.label,
                publisher=album.publisher,
                event_id=album.event_id,
                franchise_id=album.franchise_id,
                storage_drive=album.storage_drive,
                relative_path=album.relative_path,
                original_folder_name=album.original_folder_name,
            )
            self._session.add(model)
        else:
            model.title_original = album.title_original
            model.title_translated = album.title_translated
            model.release_date = album.release_date
            model.label = album.label
            model.publisher = album.publisher
            model.event_id = album.event_id
            model.franchise_id = album.franchise_id
            model.storage_drive = album.storage_drive
            model.relative_path = album.relative_path
            model.original_folder_name = album.original_folder_name

        model.category_associations.clear()
        for cat in album.categories:
            model.category_associations.append(AlbumCategoryModel(album_id=album.id, category=cat))

        model.discs.clear()
        for d in album.discs:
            disc_model = DiscModel(
                id=d.id,
                album_id=album.id,
                disc_number=d.disc_number,
                catalog_number=d.catalog_number,
                media_type=d.media_type,
                container_format=d.container_format,
                log_type=d.log_type,
                log_score=d.log_score,
            )
            for t in d.tracks:
                disc_model.tracks.append(
                    TrackModel(
                        id=t.id,
                        disc_id=d.id,
                        track_number=t.track_number,
                        title_original=t.title_original,
                        title_translated=t.title_translated,
                        duration_seconds=t.duration_seconds,
                        audio_codec=t.audio_codec,
                        video_codec=t.video_codec,
                        bit_depth=t.bit_depth,
                        sample_rate=t.sample_rate,
                        bitrate_kbps=t.bitrate_kbps,
                        bitrate_mode=t.bitrate_mode,
                    )
                )
            model.discs.append(disc_model)

        model.archives.clear()
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
            model.archives.append(arch_model)

        model.external_links.clear()
        for el in album.external_links:
            model.external_links.append(
                ExternalLinkModel(
                    id=el.id,
                    album_id=album.id,
                    site_name=el.site_name,
                    url=el.url,
                    remote_item_id=el.remote_item_id,
                )
            )

        if album.cover:
            model.cover = AlbumCoverModel(
                id=album.cover.id,
                album_id=album.id,
                storage_path=album.cover.storage_path,
                mime_type=album.cover.mime_type,
                width=album.cover.width,
                height=album.cover.height,
            )
        else:
            model.cover = None

    async def find_by_id(self, album_id: uuid.UUID) -> Album | None:
        stmt = (
            select(AlbumModel)
            .where(AlbumModel.id == album_id)
            .options(
                joinedload(AlbumModel.cover),
                selectinload(AlbumModel.category_associations),
                selectinload(AlbumModel.discs).selectinload(DiscModel.tracks),
                selectinload(AlbumModel.artist_associations).joinedload(AlbumArtistModel.artist),
                selectinload(AlbumModel.archives).selectinload(AlbumArchiveModel.links),
                selectinload(AlbumModel.external_links),
            )
        )

        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain_entity(model)

    async def find_by_category(
        self, category: LibraryCategory, limit: int = 50, offset: int = 0
    ) -> list[Album]:
        stmt = (
            select(AlbumModel)
            .join(AlbumModel.category_associations)
            .where(AlbumCategoryModel.category == category)
            .distinct()
            .order_by(AlbumModel.release_date.desc().nulls_last())
            .offset(offset)
            .limit(limit)
            .options(
                joinedload(AlbumModel.cover),
                selectinload(AlbumModel.category_associations),
                selectinload(AlbumModel.discs).selectinload(DiscModel.tracks),
                selectinload(AlbumModel.artist_associations).joinedload(AlbumArtistModel.artist),
                selectinload(AlbumModel.archives).selectinload(AlbumArchiveModel.links),
                selectinload(AlbumModel.external_links),
            )
        )

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain_entity(m) for m in models]

    async def search(
        self,
        category: LibraryCategory | None = None,
        query: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Album], int]:
        base_stmt = select(AlbumModel)

        if category is not None:
            base_stmt = base_stmt.join(AlbumModel.category_associations).where(
                AlbumCategoryModel.category == category
            )

        if query and query.strip():
            search_pattern = f"%{query.strip()}%"
            base_stmt = base_stmt.where(
                AlbumModel.title_original.ilike(search_pattern)
                | AlbumModel.title_translated.ilike(search_pattern)
                | AlbumModel.original_folder_name.ilike(search_pattern)
            )

        count_stmt = select(func.count(func.distinct(AlbumModel.id))).select_from(
            base_stmt.subquery()
        )
        total_count_result = await self._session.execute(count_stmt)
        total_count = total_count_result.scalar_one()

        # Fetch paginated items
        fetch_stmt = (
            base_stmt.distinct()
            .order_by(AlbumModel.release_date.desc().nulls_last())
            .offset(offset)
            .limit(limit)
            .options(
                joinedload(AlbumModel.cover),
                selectinload(AlbumModel.category_associations),
                selectinload(AlbumModel.discs).selectinload(DiscModel.tracks),
                selectinload(AlbumModel.artist_associations).joinedload(AlbumArtistModel.artist),
                selectinload(AlbumModel.archives).selectinload(AlbumArchiveModel.links),
                selectinload(AlbumModel.external_links),
            )
        )

        result = await self._session.execute(fetch_stmt)
        models = result.scalars().all()
        return [self._to_domain_entity(m) for m in models], total_count

    async def delete(self, album_id: uuid.UUID) -> bool:
        stmt = select(AlbumModel).where(AlbumModel.id == album_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return False

        await self._session.delete(model)
        return True

    @staticmethod
    def _to_domain_entity(model: AlbumModel) -> Album:
        domain_categories = [assoc.category for assoc in model.category_associations]

        domain_discs = []
        for d in model.discs:
            domain_tracks = [
                Track(
                    id=t.id,
                    disc_id=t.disc_id,
                    track_number=t.track_number,
                    title_original=t.title_original,
                    title_translated=t.title_translated,
                    duration_seconds=t.duration_seconds,
                    audio_codec=t.audio_codec,
                    video_codec=t.video_codec,
                    bit_depth=t.bit_depth,
                    sample_rate=t.sample_rate,
                    bitrate_kbps=t.bitrate_kbps,
                    bitrate_mode=t.bitrate_mode,
                )
                for t in d.tracks
            ]
            domain_tracks.sort(key=lambda x: x.track_number)
            domain_discs.append(
                Disc(
                    id=d.id,
                    album_id=d.album_id,
                    disc_number=d.disc_number,
                    catalog_number=d.catalog_number,
                    media_type=d.media_type,
                    container_format=d.container_format,
                    log_type=d.log_type,
                    log_score=d.log_score,
                    tracks=domain_tracks,
                )
            )
        domain_discs.sort(key=lambda x: x.disc_number)

        domain_artists = [
            Artist(
                id=assoc.artist.id,
                name_original=assoc.artist.name_original,
                name_translated=assoc.artist.name_translated,
                is_circle=assoc.artist.is_circle,
            )
            for assoc in model.artist_associations
        ]

        domain_archives = []
        for arch in model.archives:
            domain_links = [
                ArchiveLink(
                    id=lnk.id,
                    archive_id=lnk.archive_id,
                    provider_name=lnk.provider_name,
                    download_url=lnk.download_url,
                    is_active=lnk.is_active,
                )
                for lnk in arch.links
            ]
            domain_archives.append(
                AlbumArchive(
                    id=arch.id,
                    album_id=arch.album_id,
                    archive_name=arch.archive_name,
                    encryption_password=arch.encryption_password,
                    file_size_bytes=arch.file_size_bytes,
                    hash_sha256=arch.hash_sha256,
                    links=domain_links,
                )
            )

        domain_external_links = [
            ExternalLink(
                id=el.id,
                album_id=el.album_id,
                site_name=el.site_name,
                url=el.url,
                remote_item_id=el.remote_item_id,
            )
            for el in model.external_links
        ]

        domain_cover = None
        if model.cover:
            domain_cover = AlbumCover(
                id=model.cover.id,
                album_id=model.cover.album_id,
                storage_path=model.cover.storage_path,
                mime_type=model.cover.mime_type,
                width=model.cover.width,
                height=model.cover.height,
            )

        return Album(
            id=model.id,
            title_original=model.title_original,
            title_translated=model.title_translated,
            release_date=model.release_date,
            label=model.label,
            publisher=model.publisher,
            event_id=model.event_id,
            franchise_id=model.franchise_id,
            categories=domain_categories,
            storage_drive=model.storage_drive,
            relative_path=model.relative_path,
            original_folder_name=model.original_folder_name,
            created_at=model.created_at,
            updated_at=model.updated_at,
            discs=domain_discs,
            artists=domain_artists,
            archives=domain_archives,
            external_links=domain_external_links,
            cover=domain_cover,
        )
