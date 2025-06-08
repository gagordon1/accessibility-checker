WCAG_RULES_PATH = "model_context/wcag_rules.json"

WCAG_RULES_VECTOR_STORE_ID = "vs_6845e2137bf48191b4c51c5a183fa132"

INTERESTING = ("img, video, audio, input, select, textarea, button, a, [role], "
               "h1, h2, h3, h4, h5, h6, div, span, section, nav, main, header, footer, "
               "table, tr, td, th, form, label, fieldset, legend, ul, ol, li, p, "
               "[tabindex], [aria-label], [aria-labelledby], [aria-describedby], "
               "[aria-hidden], [title], iframe, canvas, svg, [onclick], [onkeydown], "
               "[role='button'], [role='link'], [role='checkbox'], [role='radio'], "
               "[role='menuitem'], [role='tab'], [role='tabpanel'], [role='dialog'], "
               "[role='alert'], [role='status'], [role='banner'], [role='navigation'], "
               "[role='main'], [role='complementary'], [role='contentinfo']")

# Additional selectors for specific accessibility checks
FOCUSABLE_ELEMENTS = ("a[href], input:not([disabled]), select:not([disabled]), "
                     "textarea:not([disabled]), button:not([disabled]), [tabindex]:not([tabindex='-1']), "
                     "iframe, object, embed, [contenteditable], audio[controls], video[controls]")

INTERACTIVE_NON_SEMANTIC = ("[onclick], [onkeydown], [onkeyup], [onkeypress], "
                           "[role='button'], [role='link'], [role='checkbox'], [role='radio']")
