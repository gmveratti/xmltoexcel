# Conversor de XML para Excel (CT-e)

Pipeline de dados fiscais que extrai informações de arquivos XML de CT-e (Conhecimento de Transporte Eletrônico) contidos em arquivos compactados (.rar / .zip) e gera uma planilha Excel (.xlsx) organizada e estilizada.

## Download

Baixe a versão mais recente na página de [Releases](../../releases):

1. Acesse a aba **Releases** deste repositório
2. Baixe o arquivo `.exe` da versão mais recente
3. Execute — não é necessário instalar Python nem dependências

## Como Usar

### 1. Abra o programa

Execute o arquivo `.exe` baixado. A interface gráfica será aberta automaticamente.

### 2. Selecione o arquivo compactado

- Clique em **"Procurar..."** ao lado do campo **"Arquivo Compactado"**
- Selecione o arquivo `.rar` ou `.zip` que contém os XMLs de CT-e
- O programa encontra XMLs em qualquer nível de subpastas e arquivos compactados aninhados

### 3. Selecione a pasta de destino

- Clique em **"Procurar..."** ao lado do campo **"Pasta de Destino"**
- Escolha onde o arquivo Excel será salvo
- Por padrão, é preenchida automaticamente com a mesma pasta do arquivo de origem

### 4. Inicie o processamento

- Clique em **"Iniciar Processamento"**
- O progresso será exibido em tempo real:
  - **Status** — fase atual (descompactação → extração → geração do Excel)
  - **Barra de progresso** — percentual de XMLs processados
  - **Contador** — ex: `Notas: 7500 / 15000 (50.0%)`
  - **Timer** — tempo total decorrido

### 5. Resultado

Ao concluir, uma janela de resumo exibirá:

- **Lidos** — total de XMLs encontrados
- **Sucesso** — quantos foram processados corretamente
- **Quarentena** — quantos falharam

O arquivo Excel gerado terá o mesmo nome do arquivo compactado (ex: `notas_fev_2025.rar` → `notas_fev_2025.xlsx`).

## Quarentena de Erros

XMLs que falharem durante o processamento são automaticamente:

1. **Copiados** para a pasta `erros_quarentena/` dentro do destino
2. **Documentados** — cada XML com erro gera um arquivo `_LOG.txt` com os detalhes da falha

Isso garante auditoria completa sem interromper o processamento dos demais arquivos.

## Campos Extraídos

O Excel gerado contém os seguintes grupos de dados do CT-e:

| Grupo | Descrição |
|-------|-----------|
| **ide** | Identificação (CFOP, série, número, data de emissão, UFs, etc.) |
| **emit** | Dados do emitente (CNPJ, IE, nome, endereço) |
| **rem** | Dados do remetente |
| **exped** | Dados do expedidor |
| **receb** | Dados do recebedor |
| **dest** | Dados do destinatário |
| **vPrest** | Valores da prestação de serviço |
| **imp / ICMS** | Impostos (CST, base de cálculo, alíquota, valor) |
| **infNFe** | Chaves das NF-e vinculadas |
| **infCarga** | Informações da carga |
| **comp_*** | Componentes do frete (colunas dinâmicas geradas automaticamente) |

- Colunas entre parênteses — ex: `(ide)`, `(emit)` — são separadores visuais pintados de cinza
- Valores numéricos são formatados no padrão contábil brasileiro (vírgula como separador decimal)
