# Política de literatura cinzenta (Artigo 1)

Cerca de metade do corpus do Artigo 1 é **literatura cinzenta** — guias
alimentares oficiais, documentos de ministérios, relatórios de organismos
internacionais. Isso é **correto e esperado** numa revisão de escopo (o JBI
recomenda a inclusão de literatura cinzenta), mas exige um procedimento
**auditável**: tipologia por endosso institucional, critério de inclusão,
apreciação AACODS e arquivamento com hash.

Esta política complementa — não substitui — a
[`docs/COPYRIGHT_AND_FULL_TEXT_POLICY.md`](COPYRIGHT_AND_FULL_TEXT_POLICY.md):
deposita-se o que é público; referencia-se por metadados o que é protegido.

## 1. Tipologia por nível de endosso institucional

| Nível | Emissor | Elegibilidade |
|------|---------|---------------|
| **1** | Governo nacional, FAO, OMS/WHO (política pública oficial) | **Elegível** |
| **2** | Sociedade científica / associação profissional (SBC, SBD, ABESO, SBH, ACLM, ADA, AHA, ESPEN…) | **Elegível** |
| 3 | Universidade / instituto de pesquisa | Elegível com apreciação AACODS |
| 4 | ONG / fundação | Caso a caso, com AACODS |
| **5** | Blog, indústria, material promocional/comercial | **Excluído** |

O nível é estimado automaticamente pelo campo `authority` (ver
`nutev.analysis.article1_coding.endorsement_tier`) a partir do emissor, e
**confirmado por um humano**. Nível 5 é excluído por padrão.

## 2. Critério de inclusão da literatura cinzenta

Um documento cinzento entra no corpus quando: (a) é de nível 1–2 (ou 3–4 com
AACODS favorável); (b) trata de nutrição do estilo de vida / qualidade da dieta /
guia alimentar / diretriz; e (c) está acessível publicamente ou pode ser
referenciado por metadados. Decisão final é **humana**.

## 3. Checklist AACODS

Cada documento cinzento é apreciado por seis critérios (campos no schema; ver
`nutev.analysis.article1_coding.aacods_fields`):

- **A**uthority (autoridade) — quem emite; o nível de endosso. *Auto-preenchido
  como `tier_N`; confirmar.*
- **A**ccuracy (acurácia) — fontes, método, revisão. *Humano.*
- **C**overage (cobertura) — escopo e limites declarados. *Humano.*
- **O**bjectivity (objetividade) — viés, interesse comercial. *Humano.*
- **D**ate currency (atualidade) — data/edição; vigência. *Auto-preenchido do
  ano; confirmar a edição.*
- **S**ignificance (relevância) — importância para a pergunta. *Humano.*

O campo `aacods_needs_human_review` é sempre `True` até um revisor concluir a
apreciação.

## 4. Arquivamento obrigatório (Trilha 1)

Links de guias oficiais **quebram** e as edições antigas **desaparecem** quando o
país publica uma nova versão. Sem uma cópia arquivada e um hash, o corpus deixa
de ser auditável. Portanto, para **todo documento da Trilha 1
(`guideline_repository`)**:

1. baixar o PDF (campo `archived_pdf_path`);
2. registrar o **SHA-256** do arquivo (campo `archived_pdf_sha256`, calculado por
   `nutev.analysis.article1_coding.sha256_of_file`);
3. registrar `official_url`, `issuing_body`, `country`, `document_version` e
   `access_date`.

O hash é o que permite provar, no futuro, que a versão analisada é exatamente
aquela — mesmo que o país troque o PDF no mesmo endereço.

## 5. Direito autoral

Deposita-se publicamente apenas o que a fonte permite. Para documentos
protegidos, o repositório guarda **metadados, URL oficial, DOI e o hash** — não o
texto integral. Ver [`docs/COPYRIGHT_AND_FULL_TEXT_POLICY.md`](COPYRIGHT_AND_FULL_TEXT_POLICY.md).
