/**
 * ChatEmptyState.tsx --- what the chat panel shows before a goal is set
 *
 * Contains:
 *   BOT: the ASCII bot the empty panel is fronted by
 *   ChatEmptyState: invites a reviewer to describe a goal
 */

const BOT = String.raw`
   ___________
  |  ^     ^  |
  |     _     |
  |___________|
     |     |
    _|     |_
`;

/**
 * Invites a reviewer to describe a goal.
 *
 * @returns The chat empty-state element.
 */
export function ChatEmptyState() {
  return (
    <div className="chat-intro">
      <pre className="chat-intro__bot" role="img" aria-label="Agentflow">
        {BOT}
      </pre>
      <p className="chat-intro__hint">
        Press <kbd>Enter</kbd> to send, <kbd>Shift</kbd>
        <kbd>Enter</kbd> for a new line
      </p>
    </div>
  );
}
