export function stripMarkdown(raw: string | null | undefined): string {
  if (!raw) return '';
  let text = raw;

  // 1. Remove fenced code blocks
  text = text.replace(/```[\s\S]*?```/g, '');

  // 2. Remove inline code
  text = text.replace(/`([^`]+)`/g, '$1');

  // 3. Remove images: ![alt](url) -> alt
  text = text.replace(/!\[(.*?)\]\(.*?\)/g, '$1');

  // 4. Remove links: [text](url) -> text
  text = text.replace(/\[(.*?)\]\(.*?\)/g, '$1');
  text = text.replace(/\[(.*?)\]\[.*?\]/g, '$1');

  // 5. Remove HTML tags
  text = text.replace(/<[^>]+>/g, '');

  // 6. Remove headers (# Heading) and setext underlines
  text = text.replace(/^#{1,6}\s+/gm, '');
  text = text.replace(/^[=-]{2,}\s*$/gm, '');

  // 7. Remove blockquotes (> quote)
  text = text.replace(/^>\s+/gm, '');

  // 8. Remove bold, italic, strikethrough: **text**, *text*, __text__, _text_, ~~text~~
  text = text.replace(/([*_~]{1,3})(\S.*?\S?)\1/g, '$2');

  // 9. Remove list item bullets (- item, * item, 1. item)
  text = text.replace(/^\s*[-*+]\s+/gm, '');
  text = text.replace(/^\s*\d+\.\s+/gm, '');

  // 10. Remove horizontal rules
  text = text.replace(/^\s*[-*_]{3,}\s*$/gm, '');

  // 11. Normalize multiple whitespace and newlines to a single space
  return text.replace(/\s+/g, ' ').trim();
}
