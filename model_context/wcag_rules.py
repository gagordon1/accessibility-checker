WCAG_RULES=[
    {"id": "1.1.1", "desc": "All non-text content must have a text alternative that serves the equivalent purpose, so users who cannot see the content can understand its meaning via assistive technologies or text equivalents."},
    {"id": "1.2.1", "desc": "For prerecorded audio-only and video-only content, provide a media alternative (e.g., transcript or audio description) so users who cannot hear or see the content can access its information."},
    {"id": "1.2.2", "desc": "Provide synchronized captions for prerecorded audio in video, ensuring that spoken words and relevant non-speech sounds are rendered as text in sync with playback."},
    {"id": "1.2.3", "desc": "Provide audio descriptions or a full transcript for prerecorded video content, enabling users who cannot see the video to understand essential visual information."},
    {"id": "1.2.4", "desc": "Ensure live audio-only content has a transcript available, so users who are deaf or hard of hearing can access the spoken information in real time."},
    {"id": "1.2.5", "desc": "Provide a media alternative or audio description for prerecorded synchronized media, ensuring all visual and auditory information is accessible via text or audio descriptions."},
    {"id": "1.2.6", "desc": "Provide sign language interpretation for prerecorded audio content when audio description alone is insufficient to convey meaning to deaf sign-language users."},
    {"id": "1.2.7", "desc": "Provide extended audio description for prerecorded video when standard audio descriptions cannot convey all essential visual details due to timing constraints."},
    {"id": "1.2.8", "desc": "Provide a media alternative or sign language interpretation for prerecorded synchronized media to support users reliant on sign language."},
    {"id": "1.2.9", "desc": "Provide an alternative for live audio-only content, presenting equivalent information in text for users who cannot hear the content."},
    {"id": "1.3.1", "desc": "Information, structure, and relationships conveyed through presentation can be programmatically determined or are available in text, allowing assistive technologies to convey the same relationships."},
    {"id": "1.3.2", "desc": "Ensure information conveyed by shape, color, size, or location is also available in text so users who cannot perceive those characteristics still receive the information."},
    {"id": "1.3.3", "desc": "Provide instructions that do not rely solely on sensory characteristics (shape, color, sound, size, orientation) so users with sensory impairments can understand them."},
    {"id": "1.3.4", "desc": "Content must be operable and understandable in both portrait and landscape orientations without losing functionality or usability."},
    {"id": "1.3.5", "desc": "Identify the purpose of input fields (e.g., name, email, address) using attributes or labels so user agents can help users complete forms accurately."},
    {"id": "1.3.6", "desc": "Identify the purpose of icons, regions, and UI components programmatically so that assistive technologies can announce their function."},
    {"id": "1.4.1", "desc": "Do not use color as the only visual means of conveying information, indicating an action, prompting a response, or distinguishing a visual element."},
    {"id": "1.4.2", "desc": "Provide controls to pause, stop, or adjust the volume of audio that plays automatically for longer than three seconds, enabling users to manage distractions."},
    {"id": "1.4.3", "desc": "Ensure text and images of text have a contrast ratio of at least 4.5:1 (3:1 for large text) so users with low vision or color deficiencies can read content."},
    {"id": "1.4.4", "desc": "Text must be resizable up to 200% without loss of content or functionality so users can enlarge text according to their needs."},
    {"id": "1.4.5", "desc": "Use images of text only when necessary; real text supports resizing, high contrast, and assistive technologies better than images."},
    {"id": "1.4.6", "desc": "Ensure enhanced contrast (7:1) for text and images of text at level AAA, except for large text (4.5:1) and incidental content."},
    {"id": "1.4.7", "desc": "For audio-only content with background sounds, ensure background sounds are at least 20 dB lower than foreground speech, or provide a way to turn background off."},
    {"id": "1.4.8", "desc": "Provide user controls to customize visual presentation (colors, spacing, font, line length) for better readability at level AAA."},
    {"id": "1.4.9", "desc": "Restrict images of text to decorative or essential cases only, ensuring content-critical text is real and accessible."},
    {"id": "1.4.10", "desc": "Content must reflow at up to 400% zoom without requiring horizontal scrolling, preserving content and functionality."},
    {"id": "1.4.11", "desc": "Non-text elements (UI components, icons, graphical objects) must have a contrast ratio of at least 3:1 against adjacent colors."},
    {"id": "1.4.12", "desc": "Ensure sufficient spacing and line height (at least 1.5x line height, 2x paragraph spacing, 0.12em letter, 0.16em word spacing) for improved readability."},
    {"id": "1.4.13", "desc": "Content revealed on hover or focus must remain visible until dismissed, focus is moved, or it becomes invalid, to allow full reading."},    
    {"id": "2.1.1", "desc": "All functionality must be operable through a keyboard interface without requiring specific timing for individual keystrokes."},
    {"id": "2.1.2", "desc": "If keyboard focus can move to a component, focus can also be moved away using only the keyboard, avoiding keyboard trapping."},
    {"id": "2.1.3", "desc": "All functionality operable by keyboard at level AAA without requiring specific timing for keystrokes."},
    {"id": "2.1.4", "desc": "Ensure character key shortcuts use at least one non-printable key, can be turned off, or are only active on focus."},
    {"id": "2.2.1", "desc": "Provide mechanisms to pause, stop, or adjust time limits so users have enough time to read and use content."},
    {"id": "2.2.2", "desc": "Users can pause, stop, or hide moving, blinking, scrolling, or auto-updating content that starts automatically and lasts more than five seconds."},
    {"id": "2.2.3", "desc": "Timing is not essential to the event or activity, except for real-time or non-interactive synchronized media at level AAA."},
    {"id": "2.2.4", "desc": "Interruptions can be postponed or suppressed by the user, except for emergencies."},
    {"id": "2.2.5", "desc": "When re-authentication is required, users can continue without data loss after re-authenticating."},
    {"id": "2.2.6", "desc": "Users are warned of timeouts and given an opportunity to extend sessions before data is lost."},
    {"id": "2.2.7", "desc": "Users can recover lost data after session timeouts or unexpected errors without manual re-entry."},
    {"id": "2.3.1", "desc": "Content does not flash more than three times in any one second period to avoid inducing seizures."},
    {"id": "2.3.2", "desc": "Content does not flash more than three times in any one second period at level AAA."},
    {"id": "2.3.3", "desc": "Animation initiated by user interaction can be disabled unless essential to functionality."},
    {"id": "2.4.1", "desc": "Provide a mechanism to bypass repeated blocks of content (skip links, landmarks) to improve navigation efficiency."},
    {"id": "2.4.2", "desc": "Web pages have descriptive titles reflecting topic or purpose."},
    {"id": "2.4.3", "desc": "Focusable components receive focus in an order that preserves meaning and operability."},
    {"id": "2.4.4", "desc": "Link purpose is clear from link text alone or its context."},
    {"id": "2.4.5", "desc": "Offer more than one way to locate a web page within a set, such as site search, table of contents, or navigation menus."},
    {"id": "2.4.6", "desc": "Headings and labels describe topic or purpose."},
    {"id": "2.4.7", "desc": "A visible focus indicator is present whenever an element receives keyboard focus."},
    {"id": "2.4.8", "desc": "Information about the user's location within a set of pages is available (breadcrumbs, section headings)."},

    {"id": "2.4.9", "desc": "A mechanism exists to identify link purpose from link text alone at level AAA."},
    {"id": "2.4.10", "desc": "Section headings are used to organize content at level AAA."},
    {"id": "2.4.11", "desc": "When focused, components are not entirely hidden by author-created content (minimum) level AA."},
    {"id": "2.4.12", "desc": "No part of the focused component is hidden by author-created content (enhanced) level AAA."},
    {"id": "2.4.13", "desc": "The focus indicator area meets size and contrast thresholds at level AAA."},

    {"id": "2.5.1", "desc": "Functions using multipoint or path-based gestures can be operated with a single pointer without path-based gestures."},
    {"id": "2.5.2", "desc": "Pointer down events do not execute functions or provide an abort/undo mechanism for single-pointer operations."},
    {"id": "2.5.3", "desc": "The accessible name for UI components includes the visible label text."},
    {"id": "2.5.4", "desc": "Functions triggered by device or user motion can also be operated via UI components, and motion can be disabled."},
    {"id": "2.5.5", "desc": "Pointer targets are at least 44×44 CSS pixels, or equivalent alternatives exist."},
    {"id": "2.5.6", "desc": "Content does not restrict use of concurrent input mechanisms such as voice, touch, and keyboard."},
    {"id": "2.5.7", "desc": "Dragging movements can be operated without dragging when not essential, level AA."},
    {"id": "2.5.8", "desc": "Pointer targets are at least 24×24 CSS pixels, with spacing rules, level AA."},
    {"id": "3.1.1", "desc": "The default human language of each web page can be programmatically determined."},
    {"id": "3.1.2", "desc": "The human language of each passage or phrase can be programmatically determined, except proper names and technical terms."},
    {"id": "3.1.3", "desc": "A mechanism identifies definitions of unusual words, idioms, and jargon at level AAA."},
    {"id": "3.1.4", "desc": "A mechanism identifies the expanded form of abbreviations at level AAA."},
    {"id": "3.1.5", "desc": "Supplemental content or simpler versions are available for text above lower secondary education level, level AAA."},
    {"id": "3.1.6", "desc": "A mechanism identifies pronunciation of words where meaning is ambiguous at level AAA."},

    {"id": "3.2.1", "desc": "Components receiving focus do not cause unexpected changes of context."},
    {"id": "3.2.2", "desc": "Changing a UI component setting does not automatically change context without prior warning."},
    {"id": "3.2.3", "desc": "Navigational mechanisms repeated on multiple pages occur in the same relative order."},
    {"id": "3.2.4", "desc": "Components with the same functionality are identified consistently across pages."},
    {"id": "3.2.5", "desc": "Changes of context are only on user request, level AAA."},
    {"id": "3.2.6", "desc": "Help mechanisms repeated across pages occur in a consistent order, level A (New in 2.2)."},  

    {"id": "3.3.1", "desc": "If an input error is detected, the item is identified and described in text so users can correct it."},
    {"id": "3.3.2", "desc": "Labels or instructions are provided when content requires user input."},
    {"id": "3.3.3", "desc": "If error suggestions are known, they are provided to users."},
    {"id": "3.3.4", "desc": "Legal, financial, and data-submission pages provide mechanisms for review, reversal, or confirmation."},
    {"id": "3.3.5", "desc": "Context-sensitive help is available, level AAA."},
    {"id": "3.3.6", "desc": "For pages requiring user submission, reversible, checked, or confirmed submission is provided, level AAA."},
    {"id": "3.3.7", "desc": "Previously entered information is auto-populated or available for selection to avoid redundant entry, level A (New)."},
    {"id": "3.3.8", "desc": "Accessible authentication avoids cognitive function tests or provides alternatives/mechanisms, level AA (New)."},
    {"id": "3.3.9", "desc": "Enhanced accessible authentication provides alternative mechanisms for cognitive tests, level AAA (New)."},
    {"id": "4.1.1", "desc": "Parsing: this criterion was removed in 2.2; markup must be well-formed to avoid legacy AT issues."},
    {"id": "4.1.2", "desc": "Name, Role, Value: UI components must expose programmatic name, role, state/value, and changes to assistive technologies."},
    {"id": "4.1.3", "desc": "Status Messages: status messages must be programmatically determinable without receiving focus, level AA."}
]
