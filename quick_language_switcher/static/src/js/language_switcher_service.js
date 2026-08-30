import { reactive } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

/** localStorage key holding the codes most recently picked on this browser. */
const RECENT_KEY = "quick_language_switcher.recent";

/** How many recently used languages are pinned near the top of the list. */
const RECENT_LIMIT = 3;

/** Distance between an ASCII capital letter and its regional indicator symbol. */
const REGIONAL_INDICATOR_OFFSET = 0x1f1e6 - 0x41;

/**
 * Best-effort mapping of an Odoo locale code to a Unicode flag emoji.
 *
 * Only a two-letter region subtag is turned into a flag; anything else
 * (no region, a UN M.49 numeric region such as `ar_001`, a script modifier
 * such as `sr@latin`) yields an empty string so the caller can fall back to
 * a neutral globe icon.
 *
 * @param {string} code locale code as stored on `res.lang`, e.g. "pt_BR"
 * @returns {string} the flag emoji, or "" when none can be derived
 */
export function flagEmoji(code) {
    const region = String(code || "").split("@")[0].split("_")[1];
    if (!region || !/^[a-zA-Z]{2}$/.test(region)) {
        return "";
    }
    return String.fromCodePoint(
        ...[...region.toUpperCase()].map((char) => char.charCodeAt(0) + REGIONAL_INDICATOR_OFFSET)
    );
}

/**
 * Read the recently used language codes for this browser.
 *
 * Reading is defensive on purpose: private windows, disabled storage and
 * hand-edited values must all degrade to "no recent language" rather than
 * break the navbar.
 *
 * @returns {string[]} most recent first
 */
export function readRecentCodes() {
    try {
        const codes = JSON.parse(browser.localStorage.getItem(RECENT_KEY) || "[]");
        return Array.isArray(codes) ? codes.filter((code) => typeof code === "string") : [];
    } catch {
        return [];
    }
}

/**
 * Push a language code to the front of the recent list, keeping it short.
 *
 * @param {string} code
 */
export function rememberRecentCode(code) {
    try {
        const codes = [code, ...readRecentCodes().filter((other) => other !== code)];
        browser.localStorage.setItem(RECENT_KEY, JSON.stringify(codes.slice(0, RECENT_LIMIT)));
    } catch {
        // Storage may be full or unavailable; remembering is best effort and
        // never worth failing a language switch over.
    }
}

/**
 * Order languages as: the current one, then the recently used ones in
 * recency order, then the rest in the alphabetical order the server sent.
 *
 * `Array.prototype.sort` is stable, so languages of equal rank keep the
 * server ordering.
 *
 * @param {Object[]} languages
 * @returns {Object[]} a new, ordered array
 */
export function sortByRecency(languages) {
    const recent = readRecentCodes();
    const rank = (lang) => {
        if (lang.is_current) {
            return -1;
        }
        const index = recent.indexOf(lang.code);
        return index === -1 ? recent.length : index;
    };
    return [...languages].sort((a, b) => rank(a) - rank(b));
}

/**
 * Shared state and behaviour of the language switcher.
 *
 * Both consumers -- the systray dropdown and the command palette provider --
 * go through this service, so the language list is fetched at most once per
 * web client session however many of them are used.
 */
export const quickLanguageSwitcherService = {
    dependencies: ["orm", "notification"],

    start(env, { orm, notification }) {
        const state = reactive({ languages: [], pendingCode: "" });
        let languagesProm = null;

        /**
         * Fetch the available languages once and cache the promise.
         *
         * @returns {Promise<Object[]>}
         */
        function loadLanguages() {
            if (!languagesProm) {
                languagesProm = orm
                    .call("res.users", "quick_language_get_available", [])
                    .then((languages) => {
                        state.languages = sortByRecency(
                            languages.map((lang) => ({ ...lang, flag: flagEmoji(lang.code) }))
                        );
                        return state.languages;
                    })
                    .catch(() => {
                        // The switcher is a convenience: when the list cannot be
                        // retrieved it simply stays empty and the navbar keeps
                        // working. Drop the cached promise so a later consumer
                        // may retry.
                        languagesProm = null;
                        return [];
                    });
            }
            return languagesProm;
        }

        /**
         * Apply a language to the current user and reload the web client.
         *
         * Concurrent calls are ignored while one is in flight, which is what
         * prevents a double click from writing the language twice.
         *
         * @param {string} code
         * @returns {Promise<boolean>} whether the switch was accepted
         */
        async function switchTo(code) {
            if (state.pendingCode || !code) {
                return false;
            }
            state.pendingCode = code;
            try {
                await orm.call("res.users", "quick_language_set", [code]);
            } catch {
                state.pendingCode = "";
                notification.add(_t("Could not change language. Please try again."), {
                    type: "danger",
                });
                return false;
            }
            rememberRecentCode(code);
            browser.location.reload();
            return true;
        }

        return { state, loadLanguages, switchTo };
    },
};

registry.category("services").add("quick_language_switcher", quickLanguageSwitcherService);
