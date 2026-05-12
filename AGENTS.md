# Diretrizes de Desenvolvimento e Arquitetura

Você atua como um Engenheiro de Software Sênior. Ao gerar, refatorar ou sugerir código, você deve **obrigatoriamente** seguir as regras arquiteturais e de design descritas neste documento.

## 1. Estrutura de Diretórios: Package by Feature
O código deve ser organizado por **funcionalidades (features)** ou domínios de negócio, e não por camadas técnicas (como `controllers/`, `services/`, `models/`). 

Cada módulo de funcionalidade deve ser autocontido, expondo apenas o necessário para o resto da aplicação.

**❌ O QUE NÃO FAZER (Package by Layer):**
├── controllers/
│   ├── InvoiceController
│   └── UserController
├── services/
│   ├── InvoiceService
│   └── UserService

**✅ O QUE FAZER (Package by Feature):**
├── invoice/                  # Tudo relacionado a faturas fica aqui
│   ├── invoice.controller.   # Entrada/Rotas
│   ├── invoice.service.      # Regras de negócio
│   ├── invoice.model.        # Entidades/Tipos
│   └── invoice.repository.   # Acesso a dados
├── user/                     # Tudo relacionado a usuários fica aqui
│   ├── user.controller.
│   ├── user.service.
│   └── user.model.

## 2. Arquitetura Modular
* **Baixo Acoplamento e Alta Coesão:** Módulos diferentes não devem acessar os detalhes de implementação uns dos outros. Se o módulo `invoice` precisa de dados do `user`, ele deve chamar um serviço ou interface pública exposta pelo módulo `user`, nunca acessar o banco de dados de `user` diretamente.
* **Injeção de Dependências:** Facilite os testes e o desacoplamento injetando as dependências (serviços, repositórios) nas classes, em vez de instanciá-las diretamente.

## 3. Orientação a Objetos (OOP) e Clean Code
* **Princípios SOLID:**
  * **SRP (Responsabilidade Única):** Cada classe, método ou função deve ter apenas um motivo para mudar.
  * **OCP (Aberto/Fechado):** O código deve ser aberto para extensão, mas fechado para modificação (use interfaces e polimorfismo).
  * **DIP (Inversão de Dependência):** Dependa de abstrações (interfaces), não de implementações concretas.
* **Encapsulamento:** Proteja o estado interno dos objetos. Use modificadores de acesso (`private`, `protected`) adequadamente e exponha apenas o que for estritamente necessário.
* **Nomenclatura Clara:** Use nomes em inglês, descritivos e sem abreviações obscuras. Classes são substantivos (ex: `PaymentProcessor`), métodos são verbos de ação (ex: `processPayment`).

## 4. Regras de Resposta da IA
1. Sempre que for pedido qualquer alteração, manutenção e implementação perguntar de deseja criaruma branch nova no projeto.
2. Usar as versões mais recentes de todos os pacotes sugeridos ou ordenado. A não ser que seja pedido explicitamente ou o contexto do projeto para usar uma versão especifica.
3. Ao sugerir a criação de um novo recurso, sempre me mostre onde os arquivos se encaixam na estrutura *Package by Feature*.
4. Evite "God Classes" (classes faz-tudo). Se um arquivo estiver passando de 200-300 linhas, sugira a divisão das responsabilidades.
5. Se você identificar um código meu que fere a modularidade ou a orientação a objetos, aponte o erro e sugira a refatoração.
6. Forneça exemplos de código limpos, com tratamento de erros adequado e tipagem forte sempre que a linguagem permitir.

# 📄 Escopo do Projeto: Conversor XML para Excel (CT-e)

## 🎯 Objetivo Principal
O **Conversor XML para Excel** é uma ferramenta de automação fiscal de alta performance desenvolvida em Python. O seu objetivo é processar lotes massivos de arquivos XML do SEFAZ (Conhecimentos de Transporte Eletrônico - CT-e e seus respectivos Eventos), extrair os dados financeiros/fiscais de forma estruturada, normalizar as nomenclaturas dinâmicas das transportadoras e exportar o resultado para uma planilha Excel pronta para a conciliação contábil.

---

## 🏗️ Arquitetura e Engenharia

O projeto foi desenhado sob os princípios de *Clean Code*, processamento paralelo e resiliência de memória para suportar cargas de trabalho do setor fiscal (fechamento de mês com +50.000 notas) sem travar a máquina do utilizador.

### 1. Motor de Processamento (Core)
* **Multiprocessamento Paralelo:** Utiliza `ProcessPoolExecutor` com distribuição em *chunks* para processar múltiplos XMLs simultaneamente em diferentes núcleos da CPU.
* **Memória O(1) na Exportação:** Implementação da biblioteca `openpyxl` em modo `write_only=True`, permitindo o fluxo direto de dados da memória para o disco, prevenindo o erro de *Out of Memory (OOM)* em lotes gigantes.
* **Deduplicação Inteligente:** O pipeline possui uma memória temporária (Set) que verifica as Chaves de Acesso (44 dígitos). Se a mesma nota for carregada duas vezes (ex: num `.zip` e solta numa pasta), o sistema descarta a duplicata silenciosamente.

### 2. Parsers de Dados (Inteligência Fiscal)
* **Performance C-Level:** As buscas na árvore do XML utilizam o motor nativo em C (`xml.etree.ElementTree` via XPath e iteração direta), reduzindo o I/O de disco a uma única leitura por ficheiro.
* **Roteador Inteligente (De-Para):** Um dicionário de sinônimos (`COMPONENTS_MAP`) analisa a tag de texto livre `<xNome>` das transportadoras e roteia variações (ex: "FRT PESO", "FRETE POR PESO") para colunas padronizadas (`comp_FRETE_PESO`), garantindo precisão matemática.
* **Soma Cumulativa:** Se uma nota apresentar múltiplas cobranças da mesma natureza (ex: dois pedágios), o *parser* soma os valores automaticamente na mesma coluna para evitar perda de dados.
* **Isolamento de Eventos:** Separa nativamente os ficheiros de CT-e padrão dos Eventos (Cancelamentos, Cartas de Correção - CC-e, Prestação em Desacordo).

### 3. Interface e Usabilidade (UI)
* **Input Híbrido / Sandboxing:** O utilizador pode selecionar ficheiros compactados (`.zip`, `.rar`) ou diretórios inteiros. O sistema clona os ficheiros para uma zona de *sandbox* temporária, garantindo que a pasta original da empresa não seja alterada ou corrompida.
* **Portabilidade (Plug & Play):** Compilado via `PyInstaller` num único `.exe` independente. O motor do WinRAR (`UnRAR.exe`) é embutido no binário, dispensando qualquer instalação prévia no computador do utilizador final.
* **Quarentena de Erros:** Ficheiros XML corrompidos ou mal formatados são isolados numa pasta de quarentena, acompanhados de um `_LOG.txt` detalhado com o *traceback* do erro, sem interromper o processamento do restante do lote.

---

## 📊 Estrutura de Exportação (Excel)

O ficheiro final é gerado com tipagem de dados estrita, garantindo que o Excel reconheça datas nativamente (`DD/MM/YYYY HH:MM:SS`) e valores como moeda:

* **Aba 1 (CTe Data):** Consolida todos os Conhecimentos de Transporte ativos, com as colunas formatadas em padrão contábil (`#,##0.00`).
* **Aba 2 (Eventos e Correções):** Log de auditoria contendo as Chaves de Acesso, Tipo de Evento (Cancelado/CC-e), Data e a Justificativa/Detalhe da alteração.

---

## 🛠️ Stack Tecnológica
* **Linguagem:** Python 3.10+
* **Interface:** Tkinter (Nativo)
* **Manipulação Excel:** `openpyxl`
* **Processamento XML:** `xml.etree.ElementTree`
* **Empacotamento & CI/CD:** `PyInstaller` integrado via GitHub Actions para compilação automatizada em ambiente Windows.

---
