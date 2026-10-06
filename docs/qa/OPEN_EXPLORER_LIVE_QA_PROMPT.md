# Prompt — QA da página real do Explorador Aberto (NutEV)

Cole o texto abaixo num agente que controle um **navegador real** (Claude no Chrome, um agente com Playwright/computer use ou uma pessoa testadora). O roteiro testa a página publicada; ele não substitui os testes automatizados do repositório.

Versão do roteiro: 2026-10-04, alinhada à reformulação visual da busca aberta (#1351): o painel de estratégia abre pelo botão "Ajustar busca", e a página não mostra mais o commit (ele fica em `/api/version`).

---

```text
Você é um testador de QA. Avalie a página pública do NutEV em um navegador real,
clicando nos botões e verificando se cada interação funciona. Seja factual: registre o
que viu, com evidência (print, texto da tela, mensagem do console ou requisição de rede).
Não suponha resultados que você não observou. Os nomes de botões citados abaixo são os
da versão atual; se algum mudou, use o equivalente e anote a diferença.

ENDEREÇOS
- Site: https://nutev.mindsperformance.com.br/
- Busca aberta: https://nutev.mindsperformance.com.br/aberto/
- Versão publicada: https://nutev.mindsperformance.com.br/api/version (anote o "commit")

REGRAS
- Não faça login, não crie conta, não peça acesso e não envie formulários de senha.
  A área privada deve continuar fechada para você.
- Faça no máximo 12 buscas no total: as fontes (Europe PMC, PubMed, OpenAlex, Crossref)
  são APIs públicas com limite de uso.
- Não altere nada fora da página. Downloads (CSV/JSON) podem ser salvos localmente.
- Teste em duas telas: desktop (~1366x900) e celular (~390x844), e no modo escuro.
- Mantenha as DevTools abertas (Console e Network) durante todo o teste.
- Mantenha a janela do navegador visível e na frente durante todo o teste. Se a aba ficar
  oculta ou minimizada, o Chrome congela a página e os prints param de funcionar.
- Faça o bloco J (celular, teclado e modo escuro) logo depois do bloco B.

PARTE 1 — RETESTE DO QUE JÁ FOI CORRIGIDO
Confirme cada item durante o roteiro (o item entre parênteses diz onde) e responda
OK/FALHA na tabela de reteste do relatório.
  R1. Usar qualquer controle do painel "Ajustar busca" (campo, português, período, ligar
      bloco, termo, sinônimo) não faz a página nem o painel pularem, e o foco fica no
      controle. Exceção aceitável: se o painel estiver rolado até o fim e o conteúdo
      encolher (por exemplo, ao desligar o português), ele sobe só o que encolheu. (C)
  R2. "Copiar link" leva período, sinônimos, blocos/termos desligados e strings editadas;
      o link aberto em outra aba refaz a mesma busca. (G3)
  R3. Uma string editada à mão continua depois de mudar outros controles; "Restaurar"
      aparece na hora; o JSON baixado traz edited_by_hand e generated_query. (C7, G2)
  R4. Depois de mudar a estratégia, os números da busca anterior aparecem como
      "desatualizado", com o aviso "A estratégia mudou desde a última busca". (C7)
  R5. "kefir kombucha" vira dois blocos (kefir AND kombucha) e o PubMed traz resultados. (H4)
  R6. "Abrir na BVS (LILACS)" com a pergunta do exemplo traz mais de 0 resultados
      (cada bloco vai como tw:(... OR ...)). Anote o total no LILACS e na coleção completa. (C9)
  R7. Um CSV qualquer e um JSON cortado são recusados com mensagem em português, e os
      resultados que estavam na tela continuam. (G4)
  R8. "a b c" não consulta as fontes e limpa os resultados e o título da busca anterior. (H5)
  R9. O Crossref recebe o sinônimo acrescentado (MedDiet). (C3)
  R10. Uma string com [tiab] mostra o aviso sobre campos do PubMed e o botão
      "Tirar os campos do PubMed das outras bases". (H2)
  R11. "Título (A–Z)" não começa por títulos com "[" ou "607-P:"; termos livres aparecem
      como "Palavra digitada"; em EN os exemplos aparecem em inglês. (D5, H1, H4)
  R12. O CSV baixado pelo NutEV, reaberto em "Abrir arquivo", volta com as mesmas obras
      (não vai tudo para a quarentena). (G4)
  R13. O JSON baixado, reaberto, informa quantos registros e duplicatas a busca original
      tinha. (G4)
  R14. No celular: o link "Entrar" aparece, os filtros começam fechados e as caixas de
      seleção e links DOI/PMID são fáceis de tocar. (J1)

PARTE 2 — ROTEIRO (para cada item: passos -> esperado -> obtido -> OK/FALHA + evidência)

A. Entrada sem login
  A1. Em janela anônima, abra o site (raiz "/"). Esperado: vai direto para /aberto/,
      sem janela de usuário/senha e sem tela de login.
  A2. Abra /aberto (sem barra). Esperado: redireciona para /aberto/.
  A3. Clique "Entrar". Esperado: abre /login.html. Na tela de login, clique
      "Buscar sem login (busca aberta)". Esperado: volta para /aberto/.
  A4. Abra /search.html e /evidence-library.html sem login. Esperado: pedem login.
      Abra /api/library. Esperado: resposta 401.
  A5. Abra /api/version. Esperado: JSON com "commit" e "environment": "production".

B. Busca por pergunta
  B1. Clique no exemplo "A dieta mediterrânea melhora o controle glicêmico no diabetes tipo 2?".
  B2. Esperado: o total de artigos, o número de bases e o tempo; por base, "N registros em
      X s" e "N encontrados", ou "falhou" com o motivo (limite 429, tempo esgotado,
      rede/CORS, erro HTTP). Scopus/Web of Science aparecem como "Disponível em outras
      fontes"; LILACS/BVS, SciELO, DOAJ e Semantic Scholar como "Disponível na busca
      completa". Nenhuma fonte pode ficar consultando para sempre.
  B3. Clique "Ajustar busca". Esperado: painel lateral com os blocos Diabetes tipo 2
      (população), Dieta mediterrânea (intervenção) e Controle glicêmico (desfecho),
      termos em inglês e português e as palavras ignoradas. Esc ou o fundo escuro fecham o
      painel.
  B4. Em "Ver consultas enviadas", cada base tem formato próprio: PubMed com [tiab];
      Europe PMC com TITLE_ABS:; OpenAlex com aspas e OR/AND; Crossref só palavras-chave;
      BVS com tw:(...) em cada bloco; SciELO com frases em português e inglês.

C. Painel "Ajustar busca"
  C1. Desligue o bloco Controle glicêmico. Esperado: ele sai das consultas.
  C2. Clique num termo de Dieta mediterrânea: ele fica riscado e sai das consultas.
      Clique de novo para voltar.
  C3. Digite "MedDiet" no campo de sinônimo do bloco e Enter. Esperado: o termo entra nas
      consultas (inclusive no Crossref) e o cursor continua no campo.
  C4. Marque o campo amplo. Esperado: o PubMed perde o [tiab] e aparece a nota sobre o
      mapeamento automático (MeSH). Volte para título e resumo.
  C5. Marque "Enviar também os termos em português". Esperado: termos em português entram
      no OpenAlex e no Europe PMC. Desmarque.
  C6. Período "de 2015". Esperado: PubMed com (2015:3000[dp]), Europe PMC com PUB_YEAR, e
      o filtro de data enviado aparece nos cartões do OpenAlex e do Crossref.
  C7. Edite à mão a consulta do PubMed. Esperado: "editada à mão", o aviso e "Restaurar"
      na hora; mudar o campo ou o período não apaga a edição; aparecem "desatualizado" e
      o aviso de estratégia alterada. "Restaurar" devolve a consulta gerada.
  C8. "Copiar" uma consulta e colar num bloco de notas: o texto é igual ao da caixa.
  C9. "Abrir no PubMed", "Abrir no Europe PMC", "Abrir na BVS (LILACS)" e "Abrir no
      SciELO": cada site abre com a busca preenchida. Compare o total do PubMed com o do
      painel. Anote os totais da BVS (LILACS e coleção completa).
  C10. "Buscar de novo". Esperado: nova busca com as alterações (no Network, o parâmetro
       term da requisição esearch.fcgi).
  C11. Depois da busca, a interpretação do PubMed aparece; anote termos "não encontrados".

D. Resultados
  D1. Cada artigo mostra o nível (A, B ou Q), o tipo documental quando houver, os links
      DOI/PMID e os temas MEV/NEV.
  D2. Abra "Detalhes" em 3 artigos: rastreabilidade, completude, eixos MEV/NEV com os termos
      encontrados, tipo documental, prioridade (a soma bate com o total) e resumo.
  D3. Abra o DOI e o PMID de 3 artigos: devem levar ao artigo certo.
  D4. Filtros (nível, tema, tipo, fonte, anos, "Somente com resumo"), isolados e
      combinados: a contagem muda de forma coerente; "Limpar filtros" volta ao total.
  D5. Ordenação: teste todas as opções; "Mais recentes" ordena por ano decrescente;
      "Título (A–Z)" começa por letras.
  D6. Com mais resultados que os exibidos, "Mostrar mais" carrega mais artigos.

E. Aba "Qualidade"
  E1. Os números batem: obras únicas + repetidos removidos + quarentena = registros
      recuperados.
  E2. Passe o mouse nas barras: dicas com contagem e %, sem sair cortadas.
  E3. Clicar num tema leva aos resultados filtrados por ele.
  E4. A versão em tabela tem os mesmos números das barras.

F. Abas "Quarentena" e "Como ler"
  F1. Quarentena: cada item mostra o motivo; vazia, mostra a mensagem de vazio.
  F2. Como ler: as seções estão legíveis e um tema abre e mostra os termos.

G. Exportar, compartilhar e reabrir
  G1. "Baixar CSV": acentos corretos, uma linha por obra, colunas de nível, eixos e pontuação.
  G2. "Baixar dados (JSON)": tem manifest.query_plan, manifest.executed_queries (com
      edited_by_hand quando houver edição), manifest.term_match_policy e records.
  G3. Depois de buscar com período, um sinônimo e uma consulta editada, "Copiar link" e
      abrir em outra aba: refaz a mesma busca (confira o term do esearch).
  G4. "Abrir arquivo": o JSON baixado ("N registros lidos" e a busca original informada);
      o CSV baixado (mesmas obras da busca); um CSV qualquer (nome,cidade) e um JSON
      cortado (mensagem em português, resultados mantidos).

H. Idioma e casos de borda
  H1. Troque para EN: interface, painel, avisos, exemplos e guia em inglês; títulos e
      resumos dos artigos no original. Volte para PT.
  H2. Busque ("mediterranean diet"[tiab]) AND diabetes: aviso de string avançada, aviso
      sobre campos do PubMed e os botões "Interpretar como pergunta" e "Tirar os campos do
      PubMed das outras bases" (este limpa as outras consultas e permite "Restaurar").
  H3. "plant-based diet vs mediterranean diet for weight loss": dieta mediterrânea vira
      comparador desligado, com aviso.
  H4. "kefir kombucha": dois blocos de "Palavra digitada", aviso de que nenhum conceito do
      vocabulário foi reconhecido, e resultados no PubMed.
  H5. "Buscar" com o campo vazio: nada acontece além do foco voltar ao campo. "a b c":
      aviso de termos não reconhecidos, nenhuma requisição às fontes e nada da busca
      anterior na tela.
  H6. "ultraprocessados e obesidade em crianças nos últimos 5 anos": período preenchido
      com o ano atual menos 5.

I. Técnico (DevTools)
  I1. Console: nenhum erro de JavaScript ou de Content Security Policy da página.
  I2. Network: só a própria origem, www.ebi.ac.uk, eutils.ncbi.nlm.nih.gov,
      api.openalex.org e api.crossref.org. Anote outros domínios e respostas 4xx/5xx.
  I3. Cookies: a busca aberta não cria cookie de autenticação.
  I4. Tempo da busca até os resultados (desktop e celular).

J. Celular e acessibilidade (logo depois do bloco B)
  J1. Em ~390px: sem rolagem horizontal; "Entrar" visível; filtros começam fechados;
      painel "Ajustar busca" ocupa a tela e fecha; alvos de toque com pelo menos 24px.
  J2. Só com teclado: Tab percorre os controles com foco visível; setas trocam as abas;
      Enter busca; Enter adiciona sinônimo; Esc fecha o painel.
  J3. Modo escuro: textos legíveis; níveis A/B/Q distinguíveis também em tons de cinza.

ENTREGA (formato do relatório)
1. Resumo de 5 linhas: funciona ou não; os 3 problemas mais graves.
2. Tabela de reteste R1–R14: ID | OK/FALHA | evidência. Para R6, os totais da BVS.
3. Tabela: ID | passo | esperado | obtido | OK/FALHA | evidência.
4. Bugs novos: título, severidade (bloqueador / alto / médio / baixo), passos para
   reproduzir, esperado vs obtido, navegador/tela, print.
5. Erros de console e de rede, copiados literalmente.
6. Sugestões de usabilidade (separadas dos bugs), cada uma com o motivo.
7. Ambiente: navegador e versão, sistema, data/hora, tamanho real da área da página e o
   commit de /api/version.
```

---

## O que este roteiro não cobre

A busca da área logada (botão "Montar estratégia a partir da pergunta" e "Usar pergunta e estratégia em nova busca" no histórico) exige login, que o testador não deve fazer. Quem tiver conta pode conferir: escrever uma pergunta, clicar no botão, ver a busca avançada preenchida sem nenhuma busca iniciada, buscar e depois restaurar pelo histórico.

## Como usar o resultado

- Bugs bloqueadores e altos: abra uma issue com o relatório (sem dados pessoais) ou cole o relatório numa sessão de desenvolvimento para correção.
- Falhas de fonte isoladas (429, tempo esgotado) não são bug da página se aparecem explicitamente; só viram bug se a página travar, esconder a falha ou mostrar "0 resultados" no lugar de "falhou".
- Diferenças pequenas de contagem entre o painel e o site da base são esperadas (indexação e data mudam); diferenças grandes merecem investigação da consulta.
