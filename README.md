# Mundo do Aspirador de Pó — Simulação Comparativa de Agentes Inteligentes

Simulação em Python que compara duas arquiteturas clássicas de agentes de Inteligência Artificial no problema do **Mundo do Aspirador de Pó**: um **agente reativo simples** e um **agente baseado em modelo**.

O projeto foi construído seguindo o formalismo **PEAS** (Performance, Environment, Actuators, Sensors) e conta com uma interface gráfica em Tkinter que exibe as duas grades lado a lado, permitindo observar em tempo real como cada agente explora o ambiente, aspira a sujeira e reage a obstáculos.

## 🎯 Objetivo

Responder à pergunta: **qual agente consegue limpar mais sujeira gastando menos pontos ao longo de uma quantidade limitada de passos?**

- **Agente Reativo Simples**: decide apenas com base na percepção atual. Se a célula está suja, aspira; caso contrário, escolhe aleatoriamente uma vizinha livre. Não possui memória.
- **Agente Baseado em Modelo**: mantém uma matriz interna de visitas e, ao se mover, prioriza a vizinha menos visitada — uma estratégia simples que tende a melhorar a cobertura espacial, mas sem garantir o caminho ótimo.

Ambos os agentes operam com **observabilidade parcial**: enxergam apenas a célula onde estão e a navegabilidade das quatro células vizinhas.

## 🛠️ Tecnologias

- Python 3.10+
- Tkinter (interface gráfica)
- NumPy (grade, geração aleatória e matriz de visitas)

## ▶️ Como executar

```bash
pip install numpy
python mundo_aspirador.py
```

Na janela, é possível:
- **Passo a Passo** — observar uma decisão por vez;
- **Iniciar / Pausar** — rodar a simulação automaticamente;
- **Recomeçar** — gerar um novo ambiente com nova seed.

## 📚 Referência

Este projeto foi desenvolvido com base no livro **"Mundo do Aspirador de Pó em Python: Guia completo para iniciantes — agentes reativos e agentes baseados em modelo"**, que apresenta o passo a passo teórico e prático da construção da simulação.

## 👥 Participantes

- Álisson Michel da Silva Miranda
- Dávisson Tiago Lima Ferreira
- José Pereira Dias Neto
- Pedro Soares Assunção Junior