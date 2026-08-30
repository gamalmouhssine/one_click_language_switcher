import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

/**
 * How many languages the palette offers before the user types anything.
 *
 * With an empty search the command palette lists every command unfiltered,
 * so a database carrying a dozen languages would otherwise drown the default
 * list. The service orders recently used languages first, so this preview is
 * exactly the handful of languages the user actually alternates between.
 */
const PALETTE_PREVIEW_LIMIT = 3;

/**
 * Offer the languages the user may switch to as command palette entries, so
 * the language can be changed by typing its name instead of opening the
 * dropdown. The current language is not offered: selecting it would be a no-op.
 *
 * The provider is asynchronous, which the palette supports; it reuses the
 * service cache, so opening the palette issues no additional RPC.
 */
registry.category("command_provider").add("quick_language_switcher", {
    async provide(env, options = {}) {
        const switcher = env.services.quick_language_switcher;
        const languages = await switcher.loadLanguages();
        if (languages.length < 2) {
            return [];
        }
        const selectable = languages.filter((lang) => !lang.is_current);
        const offered = options.searchValue
            ? selectable
            : selectable.slice(0, PALETTE_PREVIEW_LIMIT);
        return offered.map((lang) => ({
            action: () => switcher.switchTo(lang.code),
            category: "default",
            name: _t("Switch language to %s", lang.name),
        }));
    },
});
