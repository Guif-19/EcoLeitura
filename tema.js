(() => {
    const chave = "ecoleitura-tema";
    let salvo = null;
    try {
        salvo = localStorage.getItem(chave);
    } catch (_) {
        // O seletor também funciona quando o navegador bloqueia armazenamento.
    }
    let tema = salvo === "dark" || salvo === "light"
        ? salvo
        : (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    let botao;

    function atualizar() {
        const escuro = tema === "dark";
        document.documentElement.dataset.ecoleituraTema = tema;
        document.documentElement.style.colorScheme = tema;
        if (document.body && document.body.classList.contains("dark") !== escuro) {
            document.body.classList.toggle("dark", escuro);
        }
        if (botao) {
            botao.querySelector("span").textContent = escuro ? "☀" : "☾";
            botao.querySelector("strong").textContent = escuro ? "Modo claro" : "Modo escuro";
            botao.setAttribute("aria-label", escuro ? "Ativar modo claro" : "Ativar modo escuro");
            botao.title = escuro ? "Ativar modo claro" : "Ativar modo escuro";
        }
    }

    atualizar();
    document.addEventListener("DOMContentLoaded", () => {
        const barra = document.createElement("div");
        barra.className = "eco-barra-tema";
        botao = document.createElement("button");
        botao.id = "ecoleitura-alternar-tema";
        botao.type = "button";
        botao.innerHTML = '<span aria-hidden="true"></span><strong></strong>';
        botao.addEventListener("click", () => {
            tema = tema === "dark" ? "light" : "dark";
            try {
                localStorage.setItem(chave, tema);
            } catch (_) {}
            atualizar();
        });
        barra.append(botao);
        document.body.prepend(barra);
        atualizar();

        // Mantém o Gradio sincronizado com a preferência escolhida para o site.
        new MutationObserver(atualizar).observe(document.body, {
            attributes: true, attributeFilter: ["class"],
        });
    }, {once: true});

    window.addEventListener("storage", (evento) => {
        if (evento.key === chave && (evento.newValue === "dark" || evento.newValue === "light")) {
            tema = evento.newValue;
            atualizar();
        }
    });
})();
