# Conversor de XML para Excel (Alta Performance)

O **Conversor de XML para Excel** é uma solução completa de pipeline de dados fiscais desenhada para processamento massivo. O software extrai informações de arquivos XML de **CT-e** (Conhecimento de Transporte Eletrônico) e **NF-e** (Nota Fiscal Eletrônica / DANFE), gerando planilhas Excel (`.xlsx`) validadas, organizadas e prontas para a conciliação contábil.

---

## 🚀 Download e Instalação

Você pode utilizar a aplicação através do binário executável nativo para Windows já compilado, sem necessidade de se preocupar com Python ou dependências!

**Passo-a-passo para baixar (Binário `.exe`):**
1. Vá até a seção **[Releases](../../releases)** na página principal deste projeto no GitHub.
2. Expanda os *Assets* da versão mais recente.
3. Faça o Download do arquivo **`.zip`** (ex: `XMLtoEXCEL.zip`).
4. Descompacte o arquivo e execute o **`XMLtoEXCEL.exe`**.

---

## 🛠️ Como Utilizar

O sistema foi arquitetado para lidar com fechar de mês massivos (+50.000 notas) com alta velocidade e estabilidade.

### 1. Selecione a Origem dos XMLs
O sistema possui **Input Híbrido**:
- **Procurar Arquivo...**: Selecione arquivos compactados (`.rar` ou `.zip`). O motor interno faz a extração recursiva de todos os XMLs, mesmo que estejam em subpastas dentro do arquivo.
- **Procurar Pasta...**: Selecione uma diretoria inteira no seu computador. O sistema varrerá todos os arquivos XML contidos nela.

### 2. Selecione o Tipo de Documento
Escolha o modo de processamento adequado:
- **CT-e (Conhecimento de Transporte)**: Focado em fretes, impostos de transporte e componentes dinâmicos (Pedágio, Gris, Frete Peso, etc).
- **NF-e / DANFE (Nota Fiscal de Produtos)**: Focado em itens de mercadoria, com a relação 1:N (uma nota gera várias linhas no Excel, uma para cada produto).

### 3. Selecione o Destino e Inicie
- Aponte a pasta onde o Excel final será salvo.
- Clique em **"Iniciar Processamento"**. Acompanhe o progresso em tempo real pela barra e pelo cronômetro.

---

## 📊 O Que é Extraído?

### Para CT-e (Transporte):
- **Dados Fiscais**: Chave de Acesso, CFOP, Natureza da Operação, Valores de Prestação.
- **Participantes**: Emitente, Remetente, Destinatário, Expedidor, Recebedor.
- **Roteador Inteligente de Componentes**: Normaliza nomes dinâmicos das transportadoras. Ex: "FRT PESO" e "FRETE POR PESO" são somados automaticamente na coluna `comp_FRETE_PESO`.
- **Impostos**: Detalhamento completo de ICMS, ST e tributos totais.

### Para NF-e (DANFE):
- **Cabeçalho da Nota**: Dados do Emitente, Destinatário e Totais da Nota.
- **Itens de Produto**: Extração detalhada de cada item (<det>), incluindo NCM, CFOP, Unidade, Quantidade, Valor Unitário e Valor Total do Produto.
- **Impostos por Item**: Detalhamento de ICMS (CST/Origem/Base/Alíquota), IPI, PIS e COFINS para cada produto individualmente.

### Eventos e Cancelamentos:
Para ambos os tipos, se houver arquivos de **Cancelamento** ou **Carta de Correção (CC-e)** no lote, o sistema cria uma segunda aba no Excel denominada "Eventos e Correções" com todo o histórico de alterações e justificativas.

---

## ⚠️ Resiliência e Quarentena

- **Deduplicação Inteligente**: O sistema identifica chaves de acesso repetidas (mesmo que estejam em arquivos diferentes ou nomes diferentes) e mantém apenas uma ocorrência no Excel.
- **Quarentena de Erros**: XMLs corrompidos ou mal formatados não travam o processo. Eles são isolados em uma pasta `erros_quarentena/` com um arquivo `_LOG.txt` explicando o motivo técnico da falha.

---

## 🎯 Engenharia de Alta Performance

1. **Strategy Pattern**: Arquitetura modular que permite processar diferentes tipos de documentos sem acoplamento.
2. **Multiprocessamento**: Distribui a carga de trabalho por todos os núcleos da CPU.
3. **Memória O(1)**: Exportação via *Streaming* direto para o disco rígido, permitindo gerar planilhas gigantes sem estourar a memória RAM do computador.
## ⚖️ Licença

Este projeto é distribuído sob uma licença **Source Available**:
- **Uso Livre e Profissional**: Você pode baixar, usar em casa ou no trabalho e modificar o código para suas necessidades.
- **Proibição de Revenda**: É estritamente proibida a revenda ou comercialização deste software, código-fonte ou binários por terceiros.

Para mais detalhes, consulte o arquivo [LICENSE](LICENSE).
