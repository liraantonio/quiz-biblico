import flet as ft
import pandas as pd
import random
import os
import time
import threading

# ----------------------------------------------------------------------
#                       CONFIGURAÇÕES GERAIS
# ----------------------------------------------------------------------
ARQUIVO_PERGUNTAS = "quiz_biblico.xlsx"
IMG_ABERTURA = "open_00.jpg"
IMG_ICONE = "icon_00.png"

# --- Cores ---
COR_PRIMARY = "#2980B9"            # Azul Principal
COR_SECONDARY = "#F39C12"          # Laranja Destaque
COR_DESTAQUE_AVANCAR = "green"     # Botão Avançar
COR_BOTAO_ALERTA = "#E67E22"       # Laranja
COR_BOTAO_FIM = "#B22222"          # Vermelho
COR_CARD = "white"

# Cores dos Níveis
CORES_NIVEL = {
    'FÁCIL': "#00BFFF",
    'MÉDIO': "#FFA500",
    'DIFÍCIL': "#FF0000"
}

# --- Pontuação (REINSERIDA AQUI) ---
PONTOS = {
    'FÁCIL': 5,
    'MÉDIO': 10,
    'DIFÍCIL': 15
}

def carregar_perguntas():
    """Carrega as perguntas do arquivo Excel."""
    try:
        try:
            d = os.path.dirname(os.path.abspath(__file__))
            os.chdir(d)
        except: pass

        df = pd.read_excel(ARQUIVO_PERGUNTAS)
        df['Nível'] = df['Nível'].astype(str).str.upper() 
        return df.to_dict('records')
    except Exception as e:
        print(f"Erro Excel: {e}")
        return []

def main(page: ft.Page):
    # --- Configurações da Página ---
    page.title = "Exploradores da Bíblia"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#ECF0F1"
    page.scroll = ft.ScrollMode.AUTO
    page.window_width = 450
    page.window_height = 850
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.favicon = IMG_ICONE 

    # --- Variáveis de Estado ---
    estado = {
        "perguntas_selecionadas": [],
        "indice_atual": 0,
        "placar": {}, 
        "participantes": [], 
        "vez_index": 0,
        "tempo_limite": 30,
        "timer_rodando": False,
        "pontos_rodada": 0,
        "ultimo_nivel_mostrado": None,
        "modo_jogo": "Aleatório"
    }

    bd_perguntas = carregar_perguntas()
    if not bd_perguntas:
        page.add(ft.Text("ERRO CRÍTICO: Arquivo Excel não encontrado.", color="red", size=20))
        return

    # ========================================================================
    #                       TELA 0: ABERTURA
    # ========================================================================
    
    def mostrar_tela_abertura():
        page.clean()
        
        # Tenta carregar a imagem, se não der, mostra ícone
        try:
            img_widget = ft.Image(src=IMG_ABERTURA, width=350, fit=ft.ImageFit.CONTAIN)
        except:
            img_widget = ft.Icon(name="book", size=100, color=COR_PRIMARY)

        page.add(ft.Container(
            content=ft.Column([
                img_widget,
                ft.Text("Exploradores da Bíblia", size=30, weight=ft.FontWeight.BOLD, color=COR_PRIMARY, text_align=ft.TextAlign.CENTER),
                ft.Text("Quiz Interativo", size=20, color="grey"),
                ft.Container(height=30),
                ft.ElevatedButton(
                    "ENTRAR", 
                    bgcolor=COR_PRIMARY, 
                    color="white", 
                    width=200, 
                    height=60,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    on_click=lambda e: mostrar_tela_config()
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            padding=20,
            height=page.height if page.height else 800
        ))

    # ========================================================================
    #                       TELA 1: CONFIGURAÇÃO
    # ========================================================================

    dd_qtd_participantes = ft.Dropdown(
        label="Participantes", options=[ft.dropdown.Option(str(i)) for i in range(1, 6)], value="1", width=150,
        on_change=lambda e: atualizar_campos_nomes()
    )
    col_nomes = ft.Column(spacing=10)
    tf_qtd_perguntas = ft.TextField(label="Qtd. Perguntas", value="6", width=150, keyboard_type=ft.KeyboardType.NUMBER)
    tf_tempo = ft.TextField(label="Tempo (s)", value="30", width=150, keyboard_type=ft.KeyboardType.NUMBER)
    cb_facil = ft.Checkbox(label="Fácil", value=True)
    cb_medio = ft.Checkbox(label="Médio", value=True)
    cb_dificil = ft.Checkbox(label="Difícil", value=True)
    rg_modo = ft.RadioGroup(content=ft.Row([
        ft.Radio(value="Aleatório", label="Aleatório"),
        ft.Radio(value="Progressivo", label="Progressivo")
    ]), value="Aleatório")

    def atualizar_campos_nomes():
        col_nomes.controls.clear()
        qtd = int(dd_qtd_participantes.value)
        for i in range(qtd):
            col_nomes.controls.append(ft.TextField(label=f"Nome Jogador {i+1}", value=f"Equipe {i+1}", border_color=COR_PRIMARY))
        page.update()

    def mostrar_tela_config():
        page.clean()
        atualizar_campos_nomes() 
        
        btn_iniciar = ft.ElevatedButton("AVANÇAR >>", bgcolor="green", color="white", width=200, height=50, on_click=processar_configuracao)
        
        page.add(ft.Container(
            content=ft.Column([
                ft.Text("Configuração", size=30, weight=ft.FontWeight.BOLD, color=COR_PRIMARY),
                ft.Divider(),
                ft.Text("Jogadores", weight=ft.FontWeight.BOLD),
                dd_qtd_participantes, col_nomes,
                ft.Divider(),
                ft.Text("Regras", weight=ft.FontWeight.BOLD),
                ft.Row([tf_qtd_perguntas, tf_tempo], alignment=ft.MainAxisAlignment.CENTER),
                ft.Text("Níveis:", size=14),
                ft.Row([cb_facil, cb_medio, cb_dificil], alignment=ft.MainAxisAlignment.CENTER),
                ft.Text("Modo:", size=14),
                rg_modo,
                ft.Container(height=20),
                btn_iniciar
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20,
            bgcolor=COR_CARD,
            border_radius=20,
            shadow=ft.BoxShadow(blur_radius=10, color="#33000000")
        ))

    def processar_configuracao(e):
        niveis_sel = []
        if cb_facil.value: niveis_sel.append('FÁCIL')
        if cb_medio.value: niveis_sel.append('MÉDIO')
        if cb_dificil.value: niveis_sel.append('DIFÍCIL')

        if not niveis_sel:
            page.show_snack_bar(ft.SnackBar(ft.Text("Selecione um nível!")))
            return

        try:
            qtd_p = int(tf_qtd_perguntas.value)
            tempo = int(tf_tempo.value)
            if tempo < 5: raise ValueError
        except:
            page.show_snack_bar(ft.SnackBar(ft.Text("Dados inválidos!")))
            return

        nomes = [c.value.strip() for c in col_nomes.controls if c.value.strip()]
        if not nomes:
            page.show_snack_bar(ft.SnackBar(ft.Text("Preencha nomes!")))
            return

        base = [p for p in bd_perguntas if p.get('Nível') in niveis_sel]
        if len(base) < qtd_p: qtd_p = len(base)

        final_perguntas = []
        modo = rg_modo.value

        if modo == "Aleatório":
            final_perguntas = random.sample(base, qtd_p)
            random.shuffle(final_perguntas)
        else:
            p_niveis = {n: [p for p in base if p['Nível'] == n] for n in niveis_sel}
            ordem_niveis = [n for n in ['FÁCIL', 'MÉDIO', 'DIFÍCIL'] if n in niveis_sel]
            
            qtd_niveis = len(ordem_niveis)
            if qtd_niveis > 0:
                base_por_nivel = qtd_p // qtd_niveis
                resto = qtd_p % qtd_niveis
                for i, nivel in enumerate(ordem_niveis):
                    qtd_para_este = base_por_nivel + (1 if i < resto else 0)
                    if p_niveis[nivel]:
                        final_perguntas.extend(random.sample(p_niveis[nivel], min(len(p_niveis[nivel]), qtd_para_este)))

        estado.update({
            "perguntas_selecionadas": final_perguntas,
            "participantes": nomes,
            "placar": {nome: 0 for nome in nomes},
            "indice_atual": 0,
            "vez_index": 0,
            "tempo_limite": tempo,
            "modo_jogo": modo,
            "ultimo_nivel_mostrado": None
        })
        
        mostrar_tela_resumo()

    # ========================================================================
    #                       TELA 1.5: RESUMO
    # ========================================================================

    def mostrar_tela_resumo():
        page.clean()
        lista_nomes = ft.Column([ft.Text(f"• {n}", size=18) for n in estado["participantes"]])

        btn_voltar = ft.OutlinedButton("VOLTAR", width=150, on_click=lambda e: mostrar_tela_config())
        btn_comecar = ft.ElevatedButton("INICIAR", bgcolor=COR_PRIMARY, color="white", width=150, on_click=lambda e: verificar_transicao_e_iniciar())

        page.add(ft.Container(
            content=ft.Column([
                ft.Text("RESUMO", size=25, weight=ft.FontWeight.BOLD, color=COR_PRIMARY),
                ft.Divider(),
                ft.Text("Jogadores:", weight=ft.FontWeight.BOLD),
                lista_nomes,
                ft.Divider(),
                ft.Text(f"Modo: {estado['modo_jogo']}"),
                ft.Text(f"Perguntas: {len(estado['perguntas_selecionadas'])}"),
                ft.Text(f"Tempo: {estado['tempo_limite']}s"),
                ft.Container(height=20),
                ft.Row([btn_voltar, btn_comecar], alignment=ft.MainAxisAlignment.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20, bgcolor=COR_CARD, border_radius=15, width=380, shadow=ft.BoxShadow(blur_radius=10, color="#33000000")
        ))

    # ========================================================================
    #                           TELA 2: O JOGO
    # ========================================================================

    # Componentes Jogo
    txt_vez = ft.Text(value="", size=20, weight=ft.FontWeight.BOLD, color=COR_PRIMARY)
    txt_info_nivel = ft.Text(value="", size=14, color="grey")
    pb_tempo = ft.ProgressBar(width=300, value=1.0, color="green", bgcolor="#eeeeee")
    txt_pergunta = ft.Text(value="", size=20, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
    col_opcoes = ft.Column(spacing=10)
    btn_revelar = ft.ElevatedButton("VER OPÇÕES", icon="visibility", bgcolor=COR_SECONDARY, color="white", width=300, height=60)
    txt_feedback = ft.Text(value="", size=18, weight=ft.FontWeight.BOLD)
    txt_explicacao = ft.Text(value="", size=16, color="grey", text_align=ft.TextAlign.CENTER)
    btn_proxima = ft.ElevatedButton("PRÓXIMA", visible=False)

    def confirmar_saida_jogo(e):
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Encerrar Jogo"),
            content=ft.Text("Voltar para o início? Todo progresso será perdido."),
            actions=[
                ft.TextButton("Não", on_click=lambda e: page.close(dlg)),
                ft.TextButton("Sim, Sair", on_click=lambda e: encerrar_e_voltar_inicio(dlg)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dlg)

    def encerrar_e_voltar_inicio(dlg):
        page.close(dlg)
        mostrar_tela_abertura()

    def mostrar_tela_jogo():
        page.clean()
        
        header = ft.Row([
            ft.Container(), 
            ft.IconButton(icon="home", icon_color="red", tooltip="Voltar ao Início", on_click=confirmar_saida_jogo)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        page.add(ft.Container(
            content=ft.Column([
                header,
                ft.Row([txt_vez], alignment=ft.MainAxisAlignment.CENTER),
                pb_tempo,
                ft.Divider(),
                txt_info_nivel,
                ft.Container(content=txt_pergunta, padding=10),
                btn_revelar, 
                col_opcoes,  
                ft.Divider(),
                txt_feedback,
                txt_explicacao,
                ft.Container(height=10),
                btn_proxima
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=10, bgcolor=COR_CARD, border_radius=20, width=380, shadow=ft.BoxShadow(blur_radius=10, color="#33000000")
        ))
        preparar_proxima_pergunta()

    def mostrar_tela_transicao(nivel):
        page.clean()
        cor = CORES_NIVEL.get(nivel, "grey")
        page.add(ft.Container(
            content=ft.Column([
                ft.Icon(name="star", color="white", size=80),
                ft.Text(f"NÍVEL {nivel}", size=50, weight=ft.FontWeight.BOLD, color="white"),
                ft.Container(height=50),
                ft.ElevatedButton("CONTINUAR >>", color=cor, bgcolor="white", width=200, height=60, on_click=lambda e: mostrar_tela_jogo())
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=cor, width=400, height=800, alignment=ft.alignment.center, border_radius=20
        ))

    def verificar_transicao_e_iniciar():
        if estado["indice_atual"] >= len(estado["perguntas_selecionadas"]):
            mostrar_placar_final()
            return

        novo_nivel = estado["perguntas_selecionadas"][estado["indice_atual"]]['Nível']
        
        deve_mostrar = (estado["indice_atual"] == 0 or 
                       (estado["modo_jogo"] == "Progressivo" and estado["ultimo_nivel_mostrado"] != novo_nivel))
        
        if deve_mostrar:
            estado["ultimo_nivel_mostrado"] = novo_nivel
            mostrar_tela_transicao(novo_nivel)
        else:
            mostrar_tela_jogo()

    def contagem_regressiva():
        tempo = estado["tempo_limite"]
        for i in range(tempo * 10, -1, -1):
            if not estado["timer_rodando"]: return
            prog = i / (tempo * 10)
            pb_tempo.value = prog
            pb_tempo.color = "red" if prog < 0.3 else "green"
            page.update()
            time.sleep(0.1)
        
        if estado["timer_rodando"]:
            estado["timer_rodando"] = False
            processar_resposta(None, time_out=True)

    def preparar_proxima_pergunta():
        if estado["indice_atual"] >= len(estado["perguntas_selecionadas"]):
            mostrar_placar_final()
            return

        pergunta = estado["perguntas_selecionadas"][estado["indice_atual"]]
        
        txt_vez.value = f"VEZ DE: {estado['participantes'][estado['vez_index']].upper()}"
        txt_info_nivel.value = f"Pergunta {estado['indice_atual']+1}/{len(estado['perguntas_selecionadas'])} - {pergunta['Nível']}"
        txt_info_nivel.color = CORES_NIVEL.get(pergunta['Nível'], "black")
        txt_pergunta.value = pergunta['Pergunta']
        
        # AQUI ESTAVA O ERRO - AGORA CORRIGIDO COM PONTOS DEFINIDO
        estado["pontos_rodada"] = PONTOS.get(pergunta['Nível'], 5)

        col_opcoes.controls.clear()
        col_opcoes.visible = False 
        btn_revelar.visible = True 
        btn_revelar.on_click = lambda e: acao_revelar()

        opcoes = [pergunta[f'Opção {L}'] for L in ['A','B','C','D']]
        random.shuffle(opcoes)
        for op in opcoes:
            col_opcoes.controls.append(ft.OutlinedButton(text=op, width=300, height=50, on_click=lambda e, r=op: processar_resposta(r)))

        txt_feedback.value = ""
        txt_explicacao.value = ""
        btn_proxima.visible = False
        pb_tempo.value = 1.0
        page.update()

    def acao_revelar():
        btn_revelar.visible = False
        col_opcoes.visible = True
        txt_feedback.value = "Selecione a resposta CORRETA!"
        txt_feedback.color = "#00BFFF" 
        page.update()
        estado["timer_rodando"] = True
        threading.Thread(target=contagem_regressiva, daemon=True).start()

    def processar_resposta(resposta, time_out=False):
        estado["timer_rodando"] = False
        pergunta = estado["perguntas_selecionadas"][estado["indice_atual"]]
        correta = pergunta['Resposta Correta']
        
        for btn in col_opcoes.controls:
            btn.disabled = True
            if btn.text == correta: btn.style = ft.ButtonStyle(bgcolor="green", color="white")
            elif btn.text == resposta and not time_out: btn.style = ft.ButtonStyle(bgcolor="red", color="white")
        
        if time_out:
            txt_feedback.value = "TEMPO ESGOTADO! ⏰"
            txt_feedback.color = "red"
        elif resposta == correta:
            txt_feedback.value = f"CORRETO! +{estado['pontos_rodada']} pts 🎉"
            txt_feedback.color = "green"
            estado["placar"][estado["participantes"][estado["vez_index"]]] += estado["pontos_rodada"]
        else:
            txt_feedback.value = "ERRADO ❌"
            txt_feedback.color = "red"
            
        txt_explicacao.value = f"📖 {pergunta['Explicação']}"
        
        total = len(estado["perguntas_selecionadas"])
        atual = estado["indice_atual"] + 1
        if atual == total - 1:
            btn_proxima.text = "IR PARA ÚLTIMA PERGUNTA"
            btn_proxima.bgcolor = "orange"
        elif atual == total:
            btn_proxima.text = "VER PLACAR FINAL"
            btn_proxima.bgcolor = "red"
        else:
            btn_proxima.text = "PRÓXIMA PERGUNTA"
            btn_proxima.bgcolor = COR_PRIMARY

        btn_proxima.visible = True
        btn_proxima.on_click = lambda e: avancar()
        page.update()

    def avancar():
        estado["indice_atual"] += 1
        estado["vez_index"] = (estado["vez_index"] + 1) % len(estado["participantes"])
        verificar_transicao_e_iniciar()

    def mostrar_placar_final():
        page.clean()
        
        ranking = sorted(estado["placar"].items(), key=lambda x: x[1], reverse=True)
        max_score = ranking[0][1] if ranking else 0
        
        lista = ft.Column()
        for i, (nome, pts) in enumerate(ranking):
            is_champion = (pts == max_score)
            cor = "gold" if is_champion else "black"
            size = 30 if is_champion else 18
            pref = "🏆 " if is_champion else f"{i+1}º "
            
            lista.controls.append(ft.Row([
                ft.Text(f"{pref}{nome}", size=size, color=cor, weight=ft.FontWeight.BOLD),
                ft.Text(f"{pts} pts", size=size, color=cor, weight=ft.FontWeight.BOLD)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))

        btn_sair = ft.ElevatedButton("ENCERRAR (IR P/ INÍCIO)", bgcolor="red", color="white", width=250, on_click=lambda e: mostrar_tela_abertura())

        page.add(ft.Container(
            content=ft.Column([
                ft.Text("🏆 FIM DE JOGO 🏆", size=30, weight=ft.FontWeight.BOLD, color=COR_PRIMARY),
                ft.Divider(),
                lista,
                ft.Divider(),
                btn_sair
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=30, bgcolor="white", border_radius=20
        ))

    mostrar_tela_abertura()

port = int(os.environ.get("PORT", 8080))
ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0", assets_dir=".")