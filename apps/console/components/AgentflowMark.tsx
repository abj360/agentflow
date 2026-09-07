/**
 * AgentflowMark.tsx --- the Agentflow orbit mark, drawn rather than loaded
 *
 * Contains:
 *   AgentflowMark: renders the brand's circular coordinator mark as inline SVG
 */

/**
 * Renders the brand mark: a coordinator core with three agents on one orbit.
 *
 * Drawn as SVG rather than loaded as an image so it stays crisp at any size and
 * picks up the theme's own colours instead of shipping a light-mode bitmap. The
 * orbit is left open at the top so the ring reads as a flow with a direction
 * rather than as a closed badge.
 *
 * @returns The brand mark element.
 */
export function AgentflowMark() {
  return (
    <svg
      className="mark"
      viewBox="0 0 32 32"
      role="img"
      aria-label="Agentflow"
      fill="none"
    >
      <path className="mark__orbit" d="M21.5 6.47A11 11 0 1 1 10.5 6.47" />
      <path
        className="mark__spoke"
        d="M16 16L21.5 6.47M16 16L10.5 6.47M16 16v11"
      />
      <circle className="mark__agent" cx="21.5" cy="6.47" r="2.3" />
      <circle
        className="mark__agent mark__agent--light"
        cx="10.5"
        cy="6.47"
        r="2.3"
      />
      <circle className="mark__agent" cx="16" cy="27" r="2.3" />
      <circle className="mark__core" cx="16" cy="16" r="3.4" />
    </svg>
  );
}
