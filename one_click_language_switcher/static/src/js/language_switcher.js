/** @odoo-module **/

import { Component, onWillStart, useRef, useState } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

/** Above this number of languages, a search field is added to the dropdown. */
const SEARCH_THRESHOLD = 10;

/**
 * Systray entry letting the current user switch the backend language.
 *
 * All of the data and the switching itself live in the
 * `one_click_language_switcher` service, which caches the language list for the
 * whole web client session: opening and closing the dropdown never triggers
 * an extra RPC.
 */
export class LanguageSwitcher extends Component {
    static template = "one_click_language_switcher.LanguageSwitcher";
    static components = { Dropdown, DropdownItem };
    static props = {};

    setup() {
        this.switcher = useService("one_click_language_switcher");
        this.switcherState = useState(this.switcher.state);
        this.state = useState({ search: "" });
        this.searchInputRef = useRef("searchInput");

        onWillStart(() => this.switcher.loadLanguages());
    }

    /** Hide the switcher entirely when there is nothing to switch to. */
    get isAvailable() {
        return this.switcherState.languages.length > 1;
    }

    /** The active language, or undefined if it was deactivated meanwhile. */
    get currentLanguage() {
        return this.switcherState.languages.find((lang) => lang.is_current);
    }

    get currentLabel() {
        return this.currentLanguage ? this.currentLanguage.name : _t("Language");
    }

    get toggleTitle() {
        return _t("Change language");
    }

    get searchPlaceholder() {
        return _t("Search language...");
    }

    get noResultLabel() {
        return _t("No language found");
    }

    get currentLabelForScreenReader() {
        return _t("Current language");
    }

    get showSearch() {
        return this.switcherState.languages.length > SEARCH_THRESHOLD;
    }

    /** Client-side filtering on the already fetched list, by name and by code. */
    get displayedLanguages() {
        const search = this.state.search.trim().toLowerCase();
        if (!search) {
            return this.switcherState.languages;
        }
        return this.switcherState.languages.filter(
            (lang) =>
                lang.name.toLowerCase().includes(search) ||
                lang.code.toLowerCase().includes(search) ||
                (lang.iso_code || "").toLowerCase().includes(search)
        );
    }

    onSearchInput(ev) {
        this.state.search = ev.target.value;
    }

    /** Called by the Dropdown once its menu is rendered and positioned. */
    onDropdownOpened() {
        this.state.search = "";
        if (this.searchInputRef.el) {
            this.searchInputRef.el.focus();
        }
    }

    /**
     * @param {Object} lang entry coming from `one_click_language_get_available`
     */
    onLanguageSelected(lang) {
        if (lang.is_current) {
            return;
        }
        this.switcher.switchTo(lang.code);
    }
}

export const systrayItem = { Component: LanguageSwitcher };

registry.category("systray").add("one_click_language_switcher.LanguageSwitcher", systrayItem, {
    sequence: 2,
});
