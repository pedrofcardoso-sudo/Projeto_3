(() => {
    const themes = new Set([
        "claro",
        "noturno",
        "oceano",
        "floresta",
        "ameixa",
        "sunset",
    ]);
    const storageKey = "todoapi-theme";
    let selectedTheme = "claro";

    try {
        const savedTheme = window.localStorage.getItem(storageKey);
        if (themes.has(savedTheme)) {
            selectedTheme = savedTheme;
        }
    } catch {
        // The page still works when browser storage is unavailable.
    }

    document.documentElement.dataset.theme = selectedTheme;

    if (!document.querySelector("[data-theme-select]")) {
        const branding = document.querySelector("#branding");
        if (branding) {
            const controls = document.createElement("div");
            controls.className = "site-controls";

            const home = document.createElement("a");
            home.className = "home-button";
            home.href = "/";
            home.textContent = "← Início";
            controls.append(home);

            const picker = document.createElement("label");
            picker.className = "theme-picker";
            picker.htmlFor = "theme-select";

            const label = document.createElement("span");
            label.textContent = "Tema do site";
            picker.append(label);

            const select = document.createElement("select");
            select.id = "theme-select";
            select.dataset.themeSelect = "";
            [
                ["claro", "Claro"],
                ["noturno", "Noturno"],
                ["oceano", "Oceano"],
                ["floresta", "Floresta"],
                ["ameixa", "Ameixa"],
                ["sunset", "Pôr do sol"],
            ].forEach(([value, text]) => {
                const option = document.createElement("option");
                option.value = value;
                option.textContent = text;
                select.append(option);
            });
            picker.append(select);
            controls.append(picker);
            branding.append(controls);
        }
    }

    document.querySelectorAll("[data-theme-select]").forEach((selector) => {
        selector.value = selectedTheme;
        selector.addEventListener("change", () => {
            if (!themes.has(selector.value)) {
                return;
            }

            selectedTheme = selector.value;
            document.documentElement.dataset.theme = selectedTheme;
            try {
                window.localStorage.setItem(storageKey, selectedTheme);
            } catch {
                // Keep the current selection for this page even without storage.
            }
        });
    });
})();
