(() => {
    let ultimoUsuario = "";
    let agendado = false;

    function mostrarSenhas(area, campos) {
        if (area.querySelector(".eco-mostrar-senha") || !campos.length) return;
        const rotulo = document.createElement("label");
        rotulo.className = "eco-mostrar-senha";
        const controle = document.createElement("input");
        controle.type = "checkbox";
        rotulo.append(controle, document.createTextNode(campos.length > 1 ? " Mostrar senhas" : " Mostrar senha"));
        controle.addEventListener("change", () => {
            campos.forEach(campo => { campo.type = controle.checked ? "text" : "password"; });
        });
        const formulario = area.querySelector("form");
        if (formulario) {
            const enviar = formulario.querySelector('button[type="submit"]');
            if (enviar) enviar.before(rotulo);
            else formulario.append(rotulo);
        }
        else campos.at(-1).closest(".form, .block")?.after(rotulo);
    }

    function aplicar() {
        const marca = document.querySelector("#ecoleitura-login");
        const area = marca?.closest(".column");
        if (area) {
            const usuario = area.querySelector('input[type="text"]:not([data-eco-senha])');
            const senha = area.querySelector('[data-eco-senha]') || area.querySelector('input[type="password"]');
            if (senha) {
                senha.dataset.ecoSenha = "true";
                senha.autocomplete = "current-password";
                mostrarSenhas(area, [senha]);
            }
            if (usuario) usuario.autocomplete = "username";
            const erro = area.querySelector(".creds");
            if (erro) {
                const mensagem = "Usuário ou senha não conferem. Confira os dados e tente novamente.";
                if (erro.textContent !== mensagem) erro.textContent = mensagem;
                erro.setAttribute("role", "alert");
                if (usuario && !usuario.value && ultimoUsuario) {
                    usuario.value = ultimoUsuario;
                    usuario.dispatchEvent(new Event("input", {bubbles:true}));
                }
            }
        }
        const cadastro = document.querySelector(".cartao-cadastro");
        if (cadastro) {
            mostrarSenhas(cadastro, [...cadastro.querySelectorAll('#senha, #confirmacao')]);
            const erro = cadastro.querySelector('[role="alert"]');
            if (erro && !erro.dataset.focoOrientado) {
                erro.dataset.focoOrientado = "true";
                erro.tabIndex = -1;
                erro.focus();
            }
        }
        const traducoes = {"Upload file":"Enviar áudio", "Record audio":"Gravar áudio", "Select input device":"Escolher microfone", "More tabs":"Mais atividades", "Close":"Fechar"};
        for (const [original, traducao] of Object.entries(traducoes)) {
            document.querySelectorAll(`[aria-label="${original}"]`).forEach(e => e.setAttribute("aria-label", traducao));
            document.querySelectorAll(`[title="${original}"]`).forEach(e => e.title = traducao);
        }
    }

    document.addEventListener("input", evento => {
        const area = document.querySelector("#ecoleitura-login")?.closest(".column");
        if (area?.contains(evento.target) && evento.target.matches('input[type="text"]:not([data-eco-senha])')) {
            ultimoUsuario = evento.target.value;
        }
    });
    function iniciar() {
        aplicar();
        new MutationObserver(() => {
            if (agendado) return;
            agendado = true;
            queueMicrotask(() => { agendado = false; aplicar(); });
        }).observe(document.body, {childList:true, subtree:true});
    }
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar, {once:true});
    else iniciar();
})();
