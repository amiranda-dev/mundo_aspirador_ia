from typing import Any, Dict, List, Optional, Tuple
import random
import tkinter as tk

import numpy as np


# Estados possíveis de uma célula da grade.
EMPTY: int = 0
DIRT: int = 1
OBSTACLE: int = -1

# Ações possíveis dos agentes.
ACTION_ASPIRAR: str = "Aspirar"
ACTION_MOVER_NORTE: str = "Mover(Norte)"
ACTION_MOVER_SUL: str = "Mover(Sul)"
ACTION_MOVER_LESTE: str = "Mover(Leste)"
ACTION_MOVER_OESTE: str = "Mover(Oeste)"
ACTION_PARAR: str = "Permanecer_Parado"

# Cada movimento é representado por (dy, dx).
MOVIMENTOS: Dict[str, Tuple[int, int]] = {
    ACTION_MOVER_NORTE: (-1, 0),
    ACTION_MOVER_SUL: (1, 0),
    ACTION_MOVER_LESTE: (0, 1),
    ACTION_MOVER_OESTE: (0, -1),
}


class Ambiente:
    """Representa a grade, suas transições e sua pontuação."""

    def __init__(
        self,
        n: int = 30,
        p_dirt: float = 0.2,
        p_obs: float = 0.15,
        seed: Optional[int] = None,
    ) -> None:
        """Cria uma grade com sujeira e obstáculos aleatórios."""
        self.n: int = n
        self.rng: np.random.Generator = np.random.default_rng(seed)
        self.grid: np.ndarray = np.zeros((self.n, self.n), dtype=int)

        rand_vals: np.ndarray = self.rng.random((self.n, self.n))
        self.grid[rand_vals < p_obs] = OBSTACLE

        dirt_mask = (
            (rand_vals >= p_obs)
            & (rand_vals < p_obs + p_dirt)
        )
        self.grid[dirt_mask] = DIRT

        self.total_dirt: int = int(np.sum(self.grid == DIRT))
        self.aspiradas: int = 0
        self.pontuacao: int = 0

    def get_posicao_valida(self) -> Tuple[int, int]:
        """Retorna uma posição que não contém obstáculo."""
        livres = np.argwhere(self.grid != OBSTACLE)
        escolha = self.rng.choice(len(livres))
        return tuple(livres[escolha])

    def obter_percepcao(self, pos: Tuple[int, int]) -> Dict[str, Any]:
        """Retorna a percepção local disponível ao agente."""
        y, x = pos
        sujo = bool(self.grid[y, x] == DIRT)
        adjacencias: Dict[str, bool] = {}

        for acao, (dy, dx) in MOVIMENTOS.items():
            ny, nx = y + dy, x + dx

            if 0 <= ny < self.n and 0 <= nx < self.n:
                adjacencias[acao] = bool(
                    self.grid[ny, nx] != OBSTACLE
                )
            else:
                adjacencias[acao] = False

        return {
            "posicao": (y, x),
            "sujo": sujo,
            "adjacencias": adjacencias,
        }

    def executar_acao(
        self,
        pos: Tuple[int, int],
        acao: str,
    ) -> Tuple[Tuple[int, int], str]:
        """Executa uma ação e retorna nova posição e mensagem de pontuação."""
        y, x = pos

        if acao == ACTION_ASPIRAR:
            if self.grid[y, x] == DIRT:
                self.grid[y, x] = EMPTY
                self.aspiradas += 1
                self.pontuacao += 10
                return pos, "+10 (Aspirou)"

            return pos, "0 (Aspirou vazio)"

        if acao in MOVIMENTOS:
            dy, dx = MOVIMENTOS[acao]
            ny, nx = y + dy, x + dx

            if (
                0 <= ny < self.n
                and 0 <= nx < self.n
                and self.grid[ny, nx] != OBSTACLE
            ):
                self.pontuacao -= 1
                return (ny, nx), "-1 (Movimento)"

            self.pontuacao -= 5
            return pos, "-5 (Colisão)"

        return pos, "0 (Parado)"


class AgenteReativoSimples:
    """Agente sem memória, baseado em regras condição-ação."""

    def decidir(self, p: Dict[str, Any]) -> Tuple[str, str]:
        """Escolhe uma ação usando somente a percepção atual."""
        if p["sujo"]:
            return ACTION_ASPIRAR, "Célula suja -> Regra: ASPIRAR"

        livres = [
            acao
            for acao, disponivel in p["adjacencias"].items()
            if disponivel
        ]

        if livres:
            escolha = random.choice(livres)
            return escolha, f"Aleatório entre livres: {escolha}"

        return ACTION_PARAR, "Sem saídas -> PARAR"


class AgenteBaseadoEmModelo:
    """Agente com uma matriz interna que registra visitas."""

    def __init__(self, n: int = 30) -> None:
        self.n: int = n
        self.visitas: np.ndarray = np.zeros((n, n), dtype=int)

    def decidir(self, p: Dict[str, Any]) -> Tuple[str, str]:
        """Escolhe sujeira ou a vizinha livre menos visitada."""
        y, x = p["posicao"]
        self.visitas[y, x] += 1

        if p["sujo"]:
            return ACTION_ASPIRAR, "Célula suja -> ASPIRAR"

        livres = [
            acao
            for acao, disponivel in p["adjacencias"].items()
            if disponivel
        ]

        if not livres:
            return ACTION_PARAR, "Sem opções -> PARAR"

        candidatos: List[str] = []
        menor_visitas: int = np.iinfo(np.int32).max

        for acao in livres:
            dy, dx = MOVIMENTOS[acao]
            ny, nx = y + dy, x + dx
            visitas_vizinha = int(self.visitas[ny, nx])

            if visitas_vizinha < menor_visitas:
                menor_visitas = visitas_vizinha
                candidatos = [acao]
            elif visitas_vizinha == menor_visitas:
                candidatos.append(acao)

        escolha = random.choice(candidatos)
        return (
            escolha,
            f"Célula com menor visitas ({menor_visitas}): {escolha}",
        )


class InterfaceGrafica:
    """Janela Tkinter que executa e exibe os dois agentes."""

    def __init__(
        self,
        root: tk.Tk,
        n: int = 30,
        t_max: int = 100,
        seed: int = 42,
    ) -> None:
        self.root: tk.Tk = root
        self.root.title("Mundo do Aspirador NxN - Simulação PEAS")
        self.root.configure(bg="#1E1E1E")

        self.n: int = n
        self.t_max: int = t_max
        self.passo: int = 0
        self.rodando: bool = False
        self.cell_sz: int = 14
        canvas_dim = self.n * self.cell_sz

        self.env_r = Ambiente(n=n, seed=seed)
        self.agente_r = AgenteReativoSimples()
        self.pos_r = self.env_r.get_posicao_valida()

        self.env_m = Ambiente(n=n, seed=seed)
        self.agente_m = AgenteBaseadoEmModelo(n=n)
        self.pos_m = self.pos_r

        top_frame = tk.Frame(root, bg="#2D2D30", pady=8)
        top_frame.pack(fill=tk.X)

        self.lbl_status = tk.Label(
            top_frame,
            text=f"Passo: 0/{self.t_max}",
            fg="white",
            bg="#2D2D30",
            font=("Consolas", 11, "bold"),
        )
        self.lbl_status.pack(side=tk.LEFT, padx=15)

        self.btn_play = tk.Button(
            top_frame,
            text="Iniciar / Pausar",
            command=self.alternar_execucao,
            bg="#007ACC",
            fg="white",
            relief=tk.FLAT,
        )
        self.btn_play.pack(side=tk.LEFT, padx=5)

        self.btn_step = tk.Button(
            top_frame,
            text="Passo a Passo",
            command=self.executar_passo,
            bg="#3E3E42",
            fg="white",
            relief=tk.FLAT,
        )
        self.btn_step.pack(side=tk.LEFT, padx=5)

        self.btn_reset = tk.Button(
            top_frame,
            text="Recomeçar",
            command=self.reiniciar_simulacao,
            bg="#D9534F",
            fg="white",
            relief=tk.FLAT,
        )
        self.btn_reset.pack(side=tk.LEFT, padx=5)

        center_frame = tk.Frame(root, bg="#1E1E1E")
        center_frame.pack(pady=5)

        frame_r = tk.Frame(center_frame, bg="#1E1E1E")
        frame_r.grid(row=0, column=0, padx=10)

        self.lbl_r = tk.Label(
            frame_r,
            text="AGENTE REATIVO SIMPLES\nPontos: 0 | Limpeza: 0.0%",
            fg="#FF6B6B",
            bg="#1E1E1E",
            font=("Consolas", 10, "bold"),
        )
        self.lbl_r.pack()

        self.canvas_r = tk.Canvas(
            frame_r,
            width=canvas_dim,
            height=canvas_dim,
            bg="white",
            highlightthickness=1,
        )
        self.canvas_r.pack()

        frame_m = tk.Frame(center_frame, bg="#1E1E1E")
        frame_m.grid(row=0, column=1, padx=10)

        self.lbl_m = tk.Label(
            frame_m,
            text="AGENTE BASEADO EM MODELO\nPontos: 0 | Limpeza: 0.0%",
            fg="#4D96FF",
            bg="#1E1E1E",
            font=("Consolas", 10, "bold"),
        )
        self.lbl_m.pack()

        self.canvas_m = tk.Canvas(
            frame_m,
            width=canvas_dim,
            height=canvas_dim,
            bg="white",
            highlightthickness=1,
        )
        self.canvas_m.pack()

        log_frame = tk.Frame(root, bg="#1E1E1E")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        sub_log_r = tk.Frame(log_frame, bg="#1E1E1E")
        sub_log_r.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
            padx=5,
        )
        tk.Label(
            sub_log_r,
            text="Log de Ações (Reativo)",
            fg="#FF6B6B",
            bg="#1E1E1E",
            font=("Consolas", 9, "bold"),
        ).pack(anchor=tk.W)

        self.txt_log_r = tk.Text(
            sub_log_r,
            height=8,
            bg="#252526",
            fg="#CCCCCC",
            font=("Consolas", 8),
            relief=tk.FLAT,
        )
        self.txt_log_r.pack(fill=tk.BOTH, expand=True)

        sub_log_m = tk.Frame(log_frame, bg="#1E1E1E")
        sub_log_m.pack(
            side=tk.RIGHT,
            fill=tk.BOTH,
            expand=True,
            padx=5,
        )
        tk.Label(
            sub_log_m,
            text="Log de Ações (Modelo com Memória)",
            fg="#4D96FF",
            bg="#1E1E1E",
            font=("Consolas", 9, "bold"),
        ).pack(anchor=tk.W)

        self.txt_log_m = tk.Text(
            sub_log_m,
            height=8,
            bg="#252526",
            fg="#CCCCCC",
            font=("Consolas", 8),
            relief=tk.FLAT,
        )
        self.txt_log_m.pack(fill=tk.BOTH, expand=True)

        self.desenhar_grade(self.canvas_r, self.env_r, self.pos_r, "#FF6B6B")
        self.desenhar_grade(self.canvas_m, self.env_m, self.pos_m, "#4D96FF")

    def reiniciar_simulacao(self) -> None:
        """Cria dois novos ambientes usando uma nova seed."""
        self.rodando = False
        self.passo = 0
        nova_seed = random.randint(1, 99999)

        self.env_r = Ambiente(n=self.n, seed=nova_seed)
        self.agente_r = AgenteReativoSimples()
        self.pos_r = self.env_r.get_posicao_valida()

        self.env_m = Ambiente(n=self.n, seed=nova_seed)
        self.agente_m = AgenteBaseadoEmModelo(n=self.n)
        self.pos_m = self.pos_r

        self.txt_log_r.delete("1.0", tk.END)
        self.txt_log_m.delete("1.0", tk.END)

        self.lbl_status.config(text=f"Passo: 0/{self.t_max}")
        self.lbl_r.config(
            text="AGENTE REATIVO SIMPLES\nPontos: 0 | Limpeza: 0.0%"
        )
        self.lbl_m.config(
            text="AGENTE BASEADO EM MODELO\nPontos: 0 | Limpeza: 0.0%"
        )

        self.desenhar_grade(self.canvas_r, self.env_r, self.pos_r, "#FF6B6B")
        self.desenhar_grade(self.canvas_m, self.env_m, self.pos_m, "#4D96FF")

    def desenhar_grade(
        self,
        canvas: tk.Canvas,
        env: Ambiente,
        pos_agente: Tuple[int, int],
        cor_agente: str,
    ) -> None:
        """Desenha células, sujeira, obstáculos e agente."""
        canvas.delete("all")
        cs = self.cell_sz

        for y in range(self.n):
            for x in range(self.n):
                val = env.grid[y, x]
                cor = "#FFFFFF"

                if val == OBSTACLE:
                    cor = "#333333"
                elif val == DIRT:
                    cor = "#E5A93C"

                canvas.create_rectangle(
                    x * cs,
                    y * cs,
                    (x + 1) * cs,
                    (y + 1) * cs,
                    fill=cor,
                    outline="#EEEEEE",
                )

                if val == DIRT:
                    canvas.create_oval(
                        x * cs + 4,
                        y * cs + 4,
                        (x + 1) * cs - 4,
                        (y + 1) * cs - 4,
                        fill="#B27300",
                        outline="",
                    )

        ay, ax = pos_agente
        canvas.create_oval(
            ax * cs + 2,
            ay * cs + 2,
            (ax + 1) * cs - 2,
            (ay + 1) * cs - 2,
            fill=cor_agente,
            outline="white",
            width=2,
        )

    def registrar_log(self, text_widget: tk.Text, msg: str) -> None:
        """Adiciona uma mensagem e rola o log para o final."""
        text_widget.insert(tk.END, msg + "\n")
        text_widget.see(tk.END)

    def executar_passo(self) -> None:
        """Executa um passo para cada agente."""
        if self.passo >= self.t_max:
            self.rodando = False
            return

        self.passo += 1

        percepcao_r = self.env_r.obter_percepcao(self.pos_r)
        acao_r, explicacao_r = self.agente_r.decidir(percepcao_r)
        self.pos_r, score_r = self.env_r.executar_acao(
            self.pos_r,
            acao_r,
        )

        taxa_r = (
            self.env_r.aspiradas / self.env_r.total_dirt * 100
            if self.env_r.total_dirt > 0
            else 0
        )
        self.lbl_r.config(
            text=(
                "AGENTE REATIVO SIMPLES\n"
                f"Pontos: {self.env_r.pontuacao} | "
                f"Limpeza: {taxa_r:.1f}%"
            )
        )
        self.registrar_log(
            self.txt_log_r,
            (
                f"[T={self.passo:03d}] "
                f"Pos: {percepcao_r['posicao']} | "
                f"Decisão: {explicacao_r} | "
                f"Custo: {score_r}"
            ),
        )
        self.desenhar_grade(
            self.canvas_r,
            self.env_r,
            self.pos_r,
            "#FF6B6B",
        )

        percepcao_m = self.env_m.obter_percepcao(self.pos_m)
        acao_m, explicacao_m = self.agente_m.decidir(percepcao_m)
        self.pos_m, score_m = self.env_m.executar_acao(
            self.pos_m,
            acao_m,
        )

        taxa_m = (
            self.env_m.aspiradas / self.env_m.total_dirt * 100
            if self.env_m.total_dirt > 0
            else 0
        )
        self.lbl_m.config(
            text=(
                "AGENTE BASEADO EM MODELO\n"
                f"Pontos: {self.env_m.pontuacao} | "
                f"Limpeza: {taxa_m:.1f}%"
            )
        )
        self.registrar_log(
            self.txt_log_m,
            (
                f"[T={self.passo:03d}] "
                f"Pos: {percepcao_m['posicao']} | "
                f"Decisão: {explicacao_m} | "
                f"Custo: {score_m}"
            ),
        )
        self.desenhar_grade(
            self.canvas_m,
            self.env_m,
            self.pos_m,
            "#4D96FF",
        )

        self.lbl_status.config(
            text=f"Passo: {self.passo}/{self.t_max}"
        )

    def loop_animacao(self) -> None:
        """Executa passos repetidos sem bloquear a janela."""
        if self.rodando and self.passo < self.t_max:
            self.executar_passo()
            self.root.after(100, self.loop_animacao)
        elif self.passo >= self.t_max:
            self.rodando = False

    def alternar_execucao(self) -> None:
        """Inicia ou pausa a animação."""
        self.rodando = not self.rodando

        if self.rodando:
            self.loop_animacao()


if __name__ == "__main__":
    janela = tk.Tk()
    app = InterfaceGrafica(janela, n=30, t_max=100, seed=42)
    janela.mainloop()
3