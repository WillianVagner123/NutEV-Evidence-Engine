# Prompt — QA da página real do Explorador Aberto (NutEV)

Cole o texto abaixo num agente que controle um **navegador real** (Claude no Chrome, um agente com Playwright/computer use ou uma pessoa testadora). O roteiro testa a página publicada; ele não substitui os testes automatizados do repositório.

---

```text
Você é um testador de QA. Avalie a página pública do NutEV em um navegador real,
clicando nos botões e verificando se cada interação funciona. Seja factual: registre o
que viu, com evidência (print, texto da tela, mensagem do console ou requisição de rede).
Não suponha resultados que você não observou.

ENDEREÇOS
- Site: https://nutev.mindsperformance.com.br/
- Busca aberta: https://nutev.mindsperformance.com.br/aberto/

REGRAS
- Não faça login, não crie conta, não peça acesso e não envie formulários de senha.
  A área privada deve continuar fechada para você.
- Faça no máximo 12 buscas no total: as fontes (Europe PMC, PubMed, OpenAlex, Crossref)
  são APIs públicas com limite de uso.
- Não altere nada fora da página. Downloads (CSV/JSON) podem ser salvos localmente.
- Teste em duas telas: desktop (~1366x900) e celular (~390x844). Teste também o modo escuro
  do sistema, se possível.
- Mantenha as DevTools abertas (Console e Network) durante todo o teste.
- Mantenha a janela do navegador visível e na frente durante todo o teste. Se a aba ficar
  oculta ou minimizada, o Chrome congela a página e os prints param de funcionar.
- Faça o bloco J (celular, teclado e modo escuro) logo depois do bloco B, com os primeiros
  resultados na tela, para ele não ficar para o fim.

PARTE 1 — RETESTE DO QUE JÁ FOI CORRIGIDO
O QA anterior (03/10/2026) encontrou os problemas abaixo, e eles foram corrigidos. Confirme
cada um durante o roteiro (o item entre parênteses diz onde) e responda OK/FALHA na tabela
de reteste do relatório.
  R1. A página pulava (rolagem de 795 para 260) e perdia o foco a cada controle do painel
      de estratégia. Agora não pode pular nem perder o foco. (C7b)
  R2. O link compartilhado não levava a estratégia editada. Agora leva período, sinônimos,
      blocos/termos desligados e strings editadas. (G3)
  R3. A edição manual sumia ao mexer em outro controle e o "Restaurar" só aparecia depois
      de buscar de novo. Agora a edição fica até "Restaurar", que aparece na hora; o JSON
      exportado traz edited_by_hand e generated_query. (C7, G2)
  R4. Os números "na fonte" ficavam velhos sem aviso depois de editar a estratégia. Agora
      aparece "desatualizado" e o aviso "A estratégia mudou desde a última busca". (C7)
  R5. "kefir kombucha" virava a frase exata e o PubMed dava 0. Agora vira kefir AND
      kombucha. (H4)
  R6. A BVS dava 0 resultados. A string mudou para o índice padrão da BVS (sem tw:). Este é
      o único ajuste não testado contra a BVS real: anote os totais. (C9)
  R7. Um CSV qualquer era aceito e substituía os resultados; JSON inválido dava erro técnico
      em inglês. Agora o arquivo é recusado com mensagem em português e os resultados
      ficam. (G4)
  R8. "a b c" deixava na tela os resultados e o título da busca anterior. Agora limpa. (H5)
  R9. O Crossref não recebia o sinônimo acrescentado (MedDiet). Agora recebe. (C3)
  R10. Uma string com [tiab] ia a todas as bases sem aviso. Agora aparece um aviso de que as
      outras bases não entendem campos do PubMed. (H2)
  R11. Ajustes menores, confira cada um:
      - "Título (A–Z)" não começa por títulos com "[" ou "607-P:" (D5);
      - a dica do gráfico de anos não sai cortada na borda (E2);
      - "1 bloco em uso" no singular: desligue blocos até sobrar um (C1);
      - o cabeçalho fixo não cobre o título das seções quando a página rola até elas;
      - em EN, os exemplos da busca aparecem em inglês (H1);
      - os cartões do OpenAlex e do Crossref mostram o filtro de data enviado (C6);
      - a nota do Crossref explica por que o total "na fonte" é tão alto;
      - "Versões e proveniência" mostra o commit publicado e o vocabulário como "aguardando
        revisão humana especializada" (F2).

PARTE 2 — ROTEIRO COMPLETO (para cada item: passos -> esperado -> obtido -> OK/FALHA + evidência)

A. Entrada sem login
  A1. Em janela anônima, abra o site (raiz "/"). Esperado: vai direto para /aberto/,
      sem janela de usuário/senha do navegador e sem tela de login.
  A2. Abra /aberto (sem barra). Esperado: redireciona para /aberto/.
  A3. No topo, clique "Busca avançada (entrar)". Esperado: abre /login.html.
      Na tela de login, clique "Buscar sem login (busca aberta)". Esperado: volta para /aberto/.
  A4. Abra anonimamente /search.html e /evidence-library.html. Esperado: pedem login
      (área privada fechada). Abra /api/library. Esperado: resposta 401.

B. Busca por pergunta (português)
  B1. Clique no exemplo "A dieta mediterrânea melhora o controle glicêmico no diabetes tipo 2?".
  B2. Esperado em "Estado das fontes": Europe PMC, PubMed, OpenAlex e Crossref, cada um com
      "N registros em X s" e "N na fonte", OU "falhou" com o motivo (limite HTTP 429, tempo
      esgotado, falha de rede/CORS, erro HTTP). Também devem aparecer
      "Scopus / Web of Science: não consultados..." e
      "LILACS/BVS, SciELO, DOAJ, Semantic Scholar: disponíveis no Reference Engine completo".
      Anote o tempo de cada fonte. Nenhuma fonte pode ficar "consultando..." para sempre.
  B3. Painel "Como o NutEV organizou sua busca". Esperado: blocos Diabetes tipo 2
      (população), Dieta mediterrânea (intervenção) e Controle glicêmico (desfecho),
      com termos em inglês e PT; a linha "Lógica" com AND entre os blocos; e a lista de
      palavras ignoradas.
  B4. Em "Strings por base", confira se cada base tem formato próprio:
      PubMed com [tiab]; Europe PMC com TITLE_ABS:; OpenAlex com aspas e OR/AND;
      Crossref só palavras-chave; BVS e SciELO com frases em português e inglês (sem tw:).

C. Interações do painel de estratégia
  C1. Desmarque "usar" no bloco Controle glicêmico. Esperado: o bloco fica apagado e some
      das strings e da linha "Lógica".
  C2. Clique num termo (chip) de Dieta mediterrânea. Esperado: o termo fica riscado e sai
      das strings. Clique de novo para voltar.
  C3. Digite "MedDiet" em "+ sinônimo" e Enter. Esperado: o chip aparece e entra nas strings.
  C4. Marque "Ampla". Esperado: a string do PubMed perde o [tiab] e a nota sobre
      mapeamento automático (MeSH) aparece. Volte para "Título e resumo".
  C5. Marque "Enviar também os termos em português". Esperado: termos PT entram na string do
      OpenAlex/Europe PMC. Desmarque.
  C6. Preencha o período "de 2015". Esperado: o PubMed ganha (2015:3000[dp]), o Europe PMC
      ganha PUB_YEAR, e OpenAlex/Crossref mostram o filtro de data.
  C7. Edite à mão a string do PubMed. Esperado: aparecem na hora "editada à mão", o aviso
      de que a string não acompanha mais os blocos e o botão "Restaurar". Mude o campo ou o
      período: a string editada continua. Os números do PubMed passam a "desatualizado" e
      surge o aviso "A estratégia mudou desde a última busca". Restaurar devolve a string gerada.
  C7b. Role a página até "Onde procurar" e use cada controle (campo, português, período,
      "usar" de um bloco, um termo). Esperado: a página não pula e o foco fica no controle.
  C8. Clique "Copiar" e cole num bloco de notas. Esperado: o texto colado é igual ao da caixa.
  C9. Clique "Abrir no PubMed", "Abrir no Europe PMC", "Abrir na BVS (LILACS)" e
      "Abrir no SciELO". Esperado: cada site abre com a busca preenchida. No PubMed,
      compare o total exibido com o "na fonte" do painel; diferenças grandes devem ser anotadas.
      BVS: anote o total em "LILACS" e na coleção completa. Se der 0, teste no site da BVS
      três variações e anote o total de cada: (a) a string como veio; (b) a mesma string com
      tw: antes de cada parêntese, ex.: tw:("diabetes tipo 2" OR "type 2 diabetes"); (c) só o
      primeiro bloco.
  C10. Clique "Buscar novamente com esta estratégia". Esperado: nova busca usando as
       alterações (confira a string no Network: requisição esearch.fcgi, parâmetro term).
  C11. Depois da busca, abra "Como o PubMed interpretou a string". Esperado: a tradução do
       PubMed aparece; se houver "O PubMed não encontrou: ...", anote os termos.

D. Resultados
  D1. Cada cartão mostra o selo de nível (A, B ou Q), a completude "N/6", o tipo documental
      (quando houver) e "#posição · pontos".
  D2. Abra "Por que este nível? Ver a explicação completa" em 3 cartões. Esperado: blocos de
      Rastreabilidade, Completude, Eixos MEV/NEV (com termos encontrados), Tipo documental,
      Prioridade (tabela que soma o total), Proveniência e Resumo.
  D3. Clique o link DOI e o PMID de 3 registros. Esperado: abrem o artigo certo. Se o DOI
      abrir outro artigo ou der erro, anote (isso é qualidade do dado da fonte).
  D4. Filtros: marque um nível, um eixo MEV/NEV, um tipo, uma fonte, um intervalo de anos e
      "Somente com resumo", isoladamente e combinados. Esperado: a contagem
      "X de Y obras únicas" muda de forma coerente; "Limpar filtros" volta ao total.
  D5. Ordenação: teste as 4 opções. "Mais recentes" deve ordenar por ano decrescente.
  D6. Se houver mais de 30 resultados, clique "Mostrar mais". Esperado: carrega mais cartões.

E. Painel "Qualidade do dado (MEV/NEV)"
  E1. Os números devem bater: obras únicas + duplicatas unificadas + quarentena =
      registros recuperados (soma das fontes).
  E2. Passe o mouse nas barras. Esperado: tooltips com contagem e %.
  E3. Clique numa linha de eixo (ex.: Padrão mediterrâneo). Esperado: vai para
      "Resultados" filtrado por esse eixo.
  E4. Abra "Ver como tabela". Esperado: a tabela tem os mesmos números das barras.
  E5. Confira os gráficos de qualidade por fonte, completude, tipo documental e ano.

F. Abas "Quarentena" e "Como ler os níveis"
  F1. Quarentena: cada item mostra o motivo (ex.: "sem identificador válido nem URL HTTP(S)").
      Se estiver vazia, deve aparecer a mensagem de vazio.
  F2. Como ler: as seções 0 a 5 estão legíveis; em "Eixos da taxonomia MEV/NEV" um eixo
      abre e mostra os termos; "Versões e proveniência" mostra a taxonomia 2026-08-v2, o
      planejador e o commit da publicação (não "cópia local").

G. Exportar, compartilhar e reabrir
  G1. "Baixar CSV": abra no Excel/Sheets. Esperado: acentos corretos, uma linha por obra e
      as colunas de nível, eixos e pontuação.
  G2. "Baixar JSON com manifesto": confira que tem manifest.query_plan,
      manifest.executed_queries (strings enviadas a cada base) e records.
  G3. Depois de buscar com período, um sinônimo acrescentado e uma string editada, clique
      "Copiar link desta busca" e abra o link em outra aba. Esperado: refaz a mesma busca, com
      o mesmo período, o sinônimo e a string editada (confira o term do esearch no Network).
  G4. Aba "Abrir arquivo": carregue o JSON exportado. Esperado: "N registros lidos" e o
      painel preenchido. Carregue o CSV exportado. Tente um CSV qualquer (ex.: nome,cidade) e
      um JSON cortado. Esperado: mensagem de erro clara em português, sem travar, e os
      resultados que estavam na tela continuam lá.

H. Idioma e casos de borda
  H1. Troque para EN. Esperado: interface, painel de estratégia, avisos e guia em inglês;
      títulos e resumos dos artigos continuam no original. Volte para PT.
  H2. Busque `("mediterranean diet"[tiab]) AND diabetes`. Esperado: aviso de "string
      avançada" enviada literalmente e o botão "Interpretar como pergunta".
  H3. Busque "plant-based diet vs mediterranean diet for weight loss". Esperado: dieta
      mediterrânea vira Comparador desligado, com aviso.
  H4. Busque "kefir kombucha". Esperado: dois blocos livres (kefir, kombucha) combinados com
      AND, aviso de que nenhum conceito do vocabulário foi reconhecido e resultados no PubMed.
  H5. Clique "Buscar" com o campo vazio: esperado nada acontecer além do foco voltar ao campo.
      Busque "a b c": esperado o aviso "Não reconhecemos termos úteis..." no painel de
      estratégia, sem erro, sem requisições às fontes e sem os resultados da busca anterior.
  H6. "ultraprocessados e obesidade em crianças nos últimos 5 anos": esperado o período
      preenchido automaticamente (ano atual menos 5; em 2026, "de 2021").

I. Técnico (DevTools)
  I1. Console: liste qualquer erro ou aviso, especialmente "Content Security Policy" e
      erros de JavaScript. Esperado: nenhum na página /aberto/.
  I2. Network: a página só deve falar com a própria origem e com www.ebi.ac.uk,
      eutils.ncbi.nlm.nih.gov, api.openalex.org e api.crossref.org. Anote requisições
      para outros domínios e respostas 4xx/5xx.
  I3. Application > Cookies: a busca aberta não deve criar cookie de autenticação.
  I4. Tempo: quanto tempo da busca até os resultados (desktop e celular).

J. Celular e acessibilidade
  J1. Em ~390px de largura: nada corta nem cria rolagem horizontal; filtros e painéis
      utilizáveis; botões com tamanho de toque adequado.
  J2. Só com teclado: Tab percorre os controles, o foco é visível, setas trocam as abas,
      Enter busca e Enter adiciona sinônimo.
  J3. Modo escuro: textos legíveis e cores dos níveis A/B/Q distinguíveis, também em tons
      de cinza (os níveis têm letra, não só cor).

ENTREGA (formato do relatório)
1. Resumo de 5 linhas: funciona ou não; os 3 problemas mais graves.
2. Tabela de reteste R1–R11: ID | OK/FALHA | evidência. Para R6, os totais da BVS.
3. Tabela: ID | passo | esperado | obtido | OK/FALHA | evidência.
4. Bugs novos: título, severidade (bloqueador / alto / médio / baixo), passos para
   reproduzir, resultado esperado vs obtido, navegador/tela, print.
5. Erros de console e de rede, copiados literalmente.
6. Sugestões de usabilidade (separadas dos bugs), cada uma com o motivo.
7. Ambiente: navegador e versão, sistema, data/hora, tamanho real da área da página, e o
   commit mostrado em "Como ler os níveis -> Versões e proveniência".
```

---

## Como usar o resultado

- Bugs bloqueadores e altos: abra uma issue com o relatório (sem dados pessoais) ou cole o relatório numa sessão de desenvolvimento para correção.
- Falhas de fonte isoladas (429, tempo esgotado) não são bug da página se aparecem explicitamente no status; elas só viram bug se a página travar, esconder a falha ou mostrar "0 resultados" no lugar de "falhou".
- Diferenças de contagem entre o painel e o site da base são esperadas em pequena escala (indexação e data da consulta mudam); diferenças grandes merecem investigação da string.
