# Depositar no Zenodo e obter o DOI permanente

O artigo (Artigo 1) promete um **identificador permanente** para o software. O
GitHub sozinho **não** fornece isso — uma URL de repositório pode mudar ou
desaparecer. O Zenodo emite um **DOI** que aponta para uma cópia arquivada e
imutável de uma *release* específica. Este guia é o passo a passo exato.

> O `.zenodo.json` na raiz já descreve os metadados do depósito (título, autores,
> licença MIT, keywords). O Zenodo lê esse arquivo automaticamente ao arquivar a
> release, então os campos abaixo virão pré-preenchidos.

## 1. Conectar o Zenodo ao GitHub (uma vez)

1. Acesse <https://zenodo.org> e entre com **"Log in with GitHub"**.
2. Autorize o Zenodo a ver seus repositórios.
3. Vá em **Zenodo → seu nome (canto superior) → GitHub**.
4. Encontre `WillianVagner123/NutEV-Evidence-Engine` na lista e **ligue o botão
   (toggle) para ON**.

A partir daqui, toda nova *release* do GitHub gera automaticamente um depósito no
Zenodo com um DOI.

## 2. Antes de criar a release — completar os TODOs

Edite o `.zenodo.json` e o `CITATION.cff` e preencha (não invente nada):

- **ORCID** do autor (crie grátis em <https://orcid.org> se ainda não tiver).
- **Afiliação** (redação exata do PPGNH/UnB).
- Se o manuscrito do Artigo 1 já tiver DOI, adicione-o em `related_identifiers`.

## 3. Criar a release no GitHub

No GitHub: **Releases → Draft a new release**.

- **Tag:** `v1.0-artigo1` (ou a versão que você for citar — veja
  `docs/RELEASE_CHECKLIST.md`).
- **Title:** `NutEV Evidence Engine v1.0-artigo1`
- **Description:** resuma o que esta versão congela (schema, trilhas, codificação
  A/B/C/D). Pode reaproveitar o `CHANGELOG.md`.
- Clique em **Publish release**.

## 4. Obter o DOI

1. Poucos minutos após publicar a release, volte ao Zenodo → **GitHub**.
2. O repositório agora mostra um **badge de DOI**. Clique nele.
3. O Zenodo mostra **dois DOIs**:
   - **Concept DOI** (`...zenodo.XXXXXX0`) — sempre aponta para a *versão mais
     recente*. Use este para "o software em geral".
   - **Version DOI** (`...zenodo.XXXXXX1`) — aponta para *esta release exata*.
     **Use este no artigo**, porque a reprodutibilidade exige a versão exata.

## 5. Onde inserir o DOI depois de obtê-lo

Substitua os `TODO`/`XXXXXXX` nestes três lugares:

1. **`CITATION.cff`** — descomente e preencha o campo `doi:` (e o `doi:` dentro de
   `preferred-citation`).
2. **`README.md`** — troque o placeholder do **badge de DOI** no topo pelo badge
   real do Zenodo (o Zenodo fornece o Markdown pronto na página do DOI).
3. **`docs/CODE_AVAILABILITY.md`** — insira o DOI no parágrafo de disponibilidade
   de código, que é o texto que vai para o manuscrito.

## 6. Releases futuras

Cada nova release gera um **novo Version DOI**, e o Concept DOI passa a apontar
para ela. Se você citar uma versão específica no artigo, **não** atualize aquela
citação — o Version DOI antigo continua válido e imutável, que é exatamente o
ponto.

---

### Checklist rápido

- [ ] Zenodo conectado ao GitHub e toggle do repositório ON
- [ ] ORCID e afiliação preenchidos em `.zenodo.json` e `CITATION.cff`
- [ ] Release `v1.0-artigo1` publicada no GitHub
- [ ] Version DOI copiado
- [ ] DOI inserido em `CITATION.cff`, `README.md` (badge) e `docs/CODE_AVAILABILITY.md`
