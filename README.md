# Neovia — Portal de Dashboards

Portal web com dashboards de apoio à gestão da frota, construído em **Python + Streamlit**.
Os dados são lidos de uma planilha Excel (base de validação) armazenada na pasta `dados/`.

## Como executar

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

Ou duplo clique em `run.bat` (Windows).

Abra o endereço indicado no terminal (ex.: http://localhost:8501).

## Estrutura

```
dashboards/
├── app.py                 # portal com navegação entre os dashboards
├── data_loader.py         # leitura/tratamento da planilha (inclui datas em serial Excel)
├── queries.py             # carga com cache para o Streamlit
├── ui_helpers.py          # formatação, gráficos e helpers comuns
├── paginas/
│   ├── 0_home.py          # início do portal
│   ├── 1_frota.py         # visão geral da frota
│   ├── 2_revisoes.py      # revisões preventivas (a partir de GASTOS)
│   ├── 3_custos.py        # custos de peças e serviços
│   ├── 4_abastecimento.py # abastecimento financeiro e quantitativo (diesel)
│   └── 5_kpis.py          # KPIs de abastecimento (veículos leves)
├── dados/
│   └── base.xlsx          # cópia da planilha base (NÃO é versionada no Git — ignorada)
└── assets/
    ├── logo.png           # logomarca
    └── icons/             # ícones dos tipos de equipamento
```

> **Nota**: a planilha `dados/base.xlsx` contém dados da empresa e **não é incluída no repositório**
> (está no `.gitignore`). Para executar, coloque a planilha em `dados/` localmente.

## Abas da planilha utilizadas

| Aba | Uso |
|---|---|
| `EQUIPAMENTOS` | Visão geral da frota |
| `GASTOS` | Revisões preventivas e custos de peças/serviços |
| `CONSUMO DIESEL EQUIPAMENTOS` | Abastecimento — financeiro e quantitativo |
| `CONSUMO VEICULOS LEVES ETANOL` | KPIs de abastecimento |
| `VEICULOS LEVES` | Mapeamento de placa → setor/equipe |

## Estado do projeto

- **Fase de validação**: os números apresentados podem divergir dos dashboards atuais da empresa,
  pois as fontes/períodos ainda estão sendo validados.
- O dashboard **Revisões Preventivas** é alimentado pelos gastos classificados como `PREVENTIVA`.
  Dados de horímetro / plano de manutenção serão incorporados quando disponíveis na base.

## Atualizar a base de dados

Substitua o arquivo `dados/base.xlsx` pela versão mais recente da planilha e recarregue o app
(o cache expira em até 1 hora ou ao reiniciar o servidor).
