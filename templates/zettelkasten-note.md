# Zettelkasten Atomic Note Template for ChatChonk
# Version: 1.0.0
# Author: Rip Jonesy (with Factory AI assistance)
# Description: Processes segments of AI chat conversations into atomic, linkable Zettelkasten notes.

metadata:
  name: "Zettelkasten Note Creator"
  id: "zettelkasten-note-creator"
  description: "Extracts a single, core idea from a conversation segment to create an atomic Zettelkasten note."
  version: "1.0.0"
  author: "Rip Jonesy"
  category: "atomic-knowledge" # e.g., 'atomic-idea', 'concept', 'fleeting-note', 'literature-note'
  tags: ["zettelkasten", "atomic", "pkm", "second-brain", "idea-processing", "adhd-friendly"]

ai_processing:
  system_prompt: |
    You are an AI assistant specialized in the Zettelkasten method. Your task is to analyze the provided segment of an AI chat conversation and extract **a single, core idea or concept** to form an atomic, self-contained Zettelkasten note.

    The note must:
    1.  **Be Atomic:** Focus on one distinct idea, argument, or piece of information. If multiple distinct ideas are present, focus on the most prominent or the first one, and suggest others could be separate Zettels.
    2.  **Be Self-Contained:** Understandable on its own, but ready to be linked.
    3.  **Identify a Clear Title:** Create a concise, descriptive title for the Zettel that captures the essence of the core idea (typically 3-7 words).
    4.  **Explain the Core Idea:** Clearly articulate the main point in a few sentences or paragraphs.
    5.  **Provide Brief Context:** Mention where this idea originated within the conversation if relevant (e.g., "from a discussion on X").
    6.  **Identify Potential Links:** List any explicitly mentioned or strongly implied related concepts, ideas, or existing Zettel IDs (if provided in the context) from the conversation that this new Zettel could link to. Use placeholder Zettel IDs or concept titles if specific ones aren't available but a connection is clear.
    7.  **Formulate Follow-up Questions:** What 1-2 new questions or avenues for exploration does this idea spark?

    The goal is to create a building block for a personal knowledge management system.
    The output should be precise and ready for integration into a Zettelkasten.
  parameters:
    temperature: 0.5 # Lower temperature for more focused, less creative extraction
    max_tokens: 1500 # Sufficient for a single atomic note
    top_p: 0.9

template:
  frontmatter: |
    ---
    title: "{{title}}"
    id: {{timestamp_id}} # Populated by system: YYYYMMDDHHMMSS format, e.g., 20250530143255
    tags: [{{#tags}}"{{.}}", {{/tags}}, zettel]
    keywords: [{{#keywords}}"{{.}}", {{/keywords}}]
    source_conversation_id: "{{source_conversation_id | default('N/A')}}"
    source_segment_hash: "{{source_segment_hash | default('N/A')}}" # Hash of the input text segment
    related_zettels: [{{#related_zettels}}"[[{{.}}]]", {{/related_zettels}}] # List of Zettel IDs or wikilinks
    chatchonk_template_id: "zettelkasten-note-creator"
    dataview: true
    ---
  content: |
    # {{title}}
    ID: `{{timestamp_id}}`

    > [!abstract] Core Idea
    > {{core_idea_explanation}}

    ## Context
    > [!quote] Source of Idea
    > This idea emerged from a discussion about `{{context_summary | default('a specific topic')}}` in conversation `{{source_conversation_id | default('N/A')}}`.
    > {{#source_quote}}
    > *Original snippet (approximate): "{{.}}"*
    > {{/source_quote}}

    ## Connections
    > [!link] Related Concepts & Zettels
    > {{#related_connections}}
    > - **[[{{related_id | default('CONCEPT_TITLE')}}]]**: {{description_of_relation}}
    > {{/related_connections}}
    > {{^related_connections}}
    > *No direct connections identified in this segment. Consider linking to broader topics.*
    > {{/related_connections}}

    ## Questions & Further Thoughts
    > [!question] Sparked Questions
    > {{#further_questions}}
    > - {{question_text}}
    > {{/further_questions}}
    > {{^further_questions}}
    > *What are the implications of this idea? How can it be applied or challenged?*
    > {{/further_questions}}

    > [!note] Fleeting Thoughts / Meta
    > {{#fleeting_thoughts}}
    > - {{thought}}
    > {{/fleeting_thoughts}}

    ---
    Tags: {{#tags}}#{{.}} {{/tags}} #zettel

extraction_rules: # Optional, to guide AI for more precise extraction
  core_idea_extraction:
    prompt: "From the provided text segment, extract the single most important, atomic idea. Describe this core idea clearly and concisely in 1-3 sentences."
  title_generation:
    prompt: "Based on the extracted core idea, generate a short, descriptive title (ideally 3-7 words) for a Zettelkasten note."
  # Zettel ID (timestamp_id) is system-generated, so no extraction rule needed from LLM.
  related_concept_identification:
    prompt: "Identify up to 3 other concepts, topics, or potential Zettel titles mentioned or strongly implied in this segment that this core idea could link to. For each, briefly describe the nature of the relationship (e.g., 'builds upon', 'contrasts with', 'example of')."
  question_generation:
    prompt: "What 1-2 insightful follow-up questions does this core idea raise for further exploration or research?"

notes_on_tool_representation:
  obsidian: |
    - **Filename Convention:** The system should generate filenames like `{{timestamp_id}} {{title}}.md` (e.g., "20250530143255 My Atomic Idea.md"). The unique timestamp ID ensures link stability, while the title provides human readability.
    - **Frontmatter:** Fully utilized for Dataview (with `dataview: true`), tags, keywords, and linking. `related_zettels` uses wikilinks `[[YYYYMMDDHHMMSS Other Zettel Title]]` or just `[[YYYYMMDDHHMMSS]]` if the title is part of the link.
    - **Content:** Markdown is native. Callouts (`> [!abstract]`, `> [!quote]`, `> [!link]`, `> [!question]`, `> [!note]`) enhance structure and scannability.
    - **Linking:** Core to Obsidian. The `[[Wikilinks]]` in `related_zettels` and within the "Connections" section will automatically create graph connections and backlinks.
  notion: |
    - **Database Structure:** Best represented as a Notion database where each Zettel is an entry (a page).
    - **Database Properties:**
      - `Title` (Title property): The Zettel title `{{title}}`.
      - `ID` (Text or Number property): The `{{timestamp_id}}`. Can be part of the Page Title or a separate property for robustness.
      - `Tags` (Multi-select property).
      - `Keywords` (Multi-select or Text property).
      - `Source Conversation ID` (Text, URL, or Relation property if conversations are also in Notion).
      - `Related Zettels` (Relation property, linking to other entries/pages in the same Zettelkasten database).
      - `Created Date` (Created Time property, automatically set by Notion).
      - `Core Idea` (Text property, for a quick summary view in database).
    - **Page Content:** The Markdown content (from the `content` section of the template) can be pasted into the Notion page body. Notion handles Markdown conversion well.
    - **Callouts:** Notion's callout blocks can replicate the `[!abstract]`, `[!quote]`, etc., for visual structure.
    - **Linking:** Use Notion's `@` mentions or `[[` page links within the "Connections" section to link to other Zettel pages in the database.
