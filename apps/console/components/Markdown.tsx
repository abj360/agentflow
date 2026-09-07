/**
 * Markdown.tsx --- renders an agent's answer as formatted text, not asterisks
 *
 * Contains:
 *   Inline: renders one line's emphasis runs
 *   Markdown: renders a whole answer's blocks
 */

import { parseBlocks, parseInline } from "../lib/markdown";

/**
 * Renders one line's emphasis runs.
 *
 * @param props.text - The line to render.
 * @returns The line's runs as elements.
 */
function Inline({ text }: Readonly<{ text: string }>) {
  return (
    <>
      {parseInline(text).map((token, index) => {
        if (token.kind === "bold") {
          return <strong key={index}>{token.text}</strong>;
        }
        if (token.kind === "italic") {
          return <em key={index}>{token.text}</em>;
        }
        if (token.kind === "code") {
          return <code key={index}>{token.text}</code>;
        }
        return <span key={index}>{token.text}</span>;
      })}
    </>
  );
}

/**
 * Renders a whole answer as the blocks the model wrote it in.
 *
 * @param props.text - The answer, as the model wrote it.
 * @returns The formatted answer element.
 */
export function Markdown({ text }: Readonly<{ text: string }>) {
  return (
    <div className="md">
      {parseBlocks(text).map((block, index) => {
        if (block.kind === "heading") {
          const Tag = block.level <= 2 ? "h3" : "h4";
          return (
            <Tag key={index} className="md__heading">
              <Inline text={block.text} />
            </Tag>
          );
        }
        if (block.kind === "code") {
          return (
            <pre key={index} className="md__code">
              {block.text}
            </pre>
          );
        }
        if (block.kind === "bullets" || block.kind === "numbers") {
          const items = block.items.map((item, position) => (
            <li key={position}>
              <Inline text={item} />
            </li>
          ));
          return block.kind === "bullets" ? (
            <ul key={index} className="md__list">
              {items}
            </ul>
          ) : (
            <ol key={index} className="md__list">
              {items}
            </ol>
          );
        }
        return (
          <p key={index} className="md__paragraph">
            <Inline text={block.text} />
          </p>
        );
      })}
    </div>
  );
}
