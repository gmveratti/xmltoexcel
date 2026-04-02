# Conversor de XML para Excel (Alta Performance)

O **Conversor de XML para Excel** é uma solução completa de pipeline de dados fiscais desenhada para processamento massivo. O software extrai informações de arquivos XML de CT-e (Conhecimento de Transporte Eletrônico) e Eventos (Cancelamentos e Correções) que estão dentro de arquivos compactados (`.rar` ou `.zip`), gerando uma planilha Excel (`.xlsx`) validada, organizada e pronta para o setor contábil.

---

## 🚀 Download e Instalação

Você pode utilizar a aplicação através do binário executável nativo para Windows já compilado, sem necessidade de se preocupar com Python ou dependências e pastas auxiliares!

**Passo-a-passo para baixar (Binário `.exe`):**
1. Vá até a seção **[Releases](../../releases)** na página principal deste projeto no GitHub.
2. Expanda os *Assets* da versão mais recente na listagem.
3. Faça o Download apenas do arquivo **`.exe`** (ex: `Conversor_XML_Excel.exe`).
4. Dê um duplo-clique. O aplicativo rodará independentemente sem instalação, contendo seu ecossistema, motor para WinRAR isolados e interfaces em seu próprio corpo!

---

## 🛠️ Como Utilizar

O fluxo foi desenhado para processar desde pacotes enxutos (15 notas) como também varrer e validar enormes blocos contábeis trimestrais (150 mil notas).

### 1. Inicialize a Aplicação 
Ao dar um duplo clique no `.exe`, a interface em janela surgirá instanciada.

### 2. Selecione o Pacote de Origem
- Pressione o botão superior **"Procurar..."** que acompanha o campo de entrada.
- Selecione o arquivo em formato compactado (`.rar` ou `.zip`) em que os XMLs de fato estão.
- **Diferencial (Busca Recursiva)**: Se dentro do seu `.zip` houver inúmeras outras pastas com outros subarquivos compactados, não há problemas. Nossa *engine* faz cascateamento de subníveis abrindo tudo e sugando exclusivamente XMLs reais.

### 3. Selecione o Destino do Relatório (.xlsx)
- Pressione **"Procurar..."** na base inferior para apontar onde deseja que seu arquivo contábil definitivo seja salvo. *(Como conveniência, por padrão, o sistema irá querer sugerir a mesma localização da origem).*

### 4. Execute a Análise
Pressione com convicção **"Iniciar Processamento"**. Uma nova centralização ocorrerá em tela onde exibimos ao usuário final:
- Os logs visuais com qual estágio nos deparamos agilmente (*"Buscando Arquivos", "Transferência em Paralelo", etc.*).
- Uma **Barra de Progresso** real com totalizador extraído `Ex: 27150/30000 (90%)` associada também a um cronômetro na ponta oposta validando o seu tempo.
  *(A arquitetura também é munida de uma verificação que reage e cancela as multithreads de forma imediata salvando lixos comissionados caso o cancelamento do processo aconteça acidentalmente via fechar botão vermelho `[X]`).*

---

## ⚠️ Quarentena e Tratativa de Erros

A resiliência matemática nos prova que nem todo documento baixado da nuvem do emissor vem correto ou atinge a integridade perfeita.

- **Um Erro nunca trava a Linha**: Um XML em corrupção absoluta passará sem travar as milhares de outras notas ao redor.
- **Rastreabilidade Fiel e Pasta "erros_quarentena/"**: O documento violado é guardado no mesmo destino de Excel mas em uma central de quarentena. Ao lado de seu CPF corrompido ou erro real nas tags, será instanciado fisicamente um arquivo `.txt` como  `_LOG.txt` provando e dedurando para você por que aquela unidade contábil individual não serviu ou onde ela se encontra destruída.

---

## 📊 Estruturação e Colunas Finais Excel

O resultado é gerado e espelhado com o nome exato original. Ex `Faturamento.zip -> Faturamento.xlsx`. E em sua anatomia o projeto tem a premissa de desconstruir o Conhecimento em:

- **`(ide)`**: Informações base, Numerações fiscais.
- **`(emit, rem, dest... etc)`**: Distribuidor Operacional entre Quem Paga e pra Onde Vai.
- **`Bloco de Valoração e Taxação:`**: Extrema fidelidade de ICMS, STs ou Variáveis, com o adendo que a inteligência artificial da aplicação reza por manter todas colunas pre-formatadas perfeitamente para contabilização real *(R$, vírgula no decimal para Excel e Google Sheets `#,#0.00` permitindo equações em blocos e análises brutas!)*.
- **`(Abas e MultiSheets)`**: Caso localizadas notas em correções textuais (Cancelamento, Substituição Fria, Eventos Eletrônicos), ele abrirá de modo higiênico uma nova aba exclusiva no Excel sem sujar a massa mestra principal.

---

## 🎯 Escopo Geral do Projeto & Engenharia

Este projeto não é um simples leitor de XML; foi arquitetado sob rigorosas validações de engenharia para lidar com imensos lotes de dados sem perda de estabilidade:

1. **Proteção OOM (Out Of Memory):** Processamento via multiprocessamento (`chunksize`) bloqueia o carregamento gigantesco de arquivos que poderiam sobrecarregar o sistema operacional ou estourar a memória RAM ao processar milhares de notas simultâneas.
2. **Motor Híbrido de Parsing:** A varredura de árvores XML foi otimizada para mesclar iterações nativas do `ElementTree` via linguagem C para garantir altíssima velocidade cirúrgica nas tags.
3. **Escrita Contínua (*Write-Only*):** A geração do arquivo Excel acontece utilizando modo `write_only` da biblioteca nativa, construindo a planilha inteira como um *streaming log* direto no disco rígido sem escalar consumo da RAM.
4. **Portabilidade Universal:** Ferramentas (Como o extrator WinRAR subjacente na pasta `bin/`) ficam embutidas e prontas para uso via detecção inteligente de path, ou nativas do OS, se existirem na máquina.
5. **Autocorreção e "Funil Inteligente":** Contém algoritmos padronizados na extração que entendem e somam acumulativamente rubricas análogas de transportadoras (ex: `Pedagio 1` + `Pedagio 2` tornaram-se a consolidante oficial `comp_PEDAGIO`).

