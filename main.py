import flet as ft
import pandas as pd
import random
import os
import time
import threading

# ----------------------------------------------------------------------
#                       CONFIGURAÇÕES VISUAIS E GERAIS
# ----------------------------------------------------------------------
ARQUIVO_PERGUNTAS = "quiz_biblico.xlsx"
TAMANHO_JANELA_QUIZ = "1200x850"

# --- Cores ---
COR_PRIMARY = "#2980B9"            # Azul Principal
COR_SECONDARY = "#F39C12"          # Laranja Destaque
COR_DESTAQUE_VEZ = "#4C00FF"       # Roxo/Azul vibrante
COR_DESTAQUE_AVANCAR = "green"     # Botão Avançar
COR_BOTAO_ALERTA = "#E67E22"       # Laranja (Penúltima)
COR_BOTAO_FIM = "#B22222"          # Vermelho (Fim)
COR_BOTAO_REVELAR = "#D35400"      # Cor do botão para revelar
COR_CARD = "white"

# Cores dos Níveis
CORES_NIVEL = {
    'FÁCIL': "#00BFFF",   # Azul Claro
    'MÉDIO': "#FFA500",   # Laranja
    'DIFÍCIL': "#FF0000"  # Vermelho
}

# --- Pontuação ---
PONTOS = {
    'FÁCIL': 5,
    'MÉDIO': 10,
    'DIFÍCIL': 15
}

# --- Tamanhos de Fonte ---
FONT_VEZ_TEMPO = 50        
FONT_PERGUNTA = 32         
FONT_OPCOES = 30           
FONT_PLACAR_TITULO = 25    
FONT_PLACAR_ITEM = 20      
FONT_NIVEL_TEXTO = 24      
FONT_NIVEL_VALOR = 24      
FONT_AVISO_GIANTE = 60     
FONT_CAMPEAO = 50          

# ----------------------------------------------------------------------
#                       FUNÇÕES E CLASSE PRINCIPAL
# ----------------------------------------------------------------------

def carregar_perguntas(caminho_arquivo):
    """Carrega as perguntas do arquivo Excel."""
    try:
        # Tenta ajustar diretório se necessário
        try:
            d = os.path.dirname(os.path.abspath(__file__))
            os.chdir(d)
        except: pass

        df = pd.read_excel(caminho_arquivo)
        df['Nível'] = df['Nível'].astype(str).str.upper() 
        perguntas = df.to_dict('records')
        return perguntas
    except Exception as e:
        print(f"Erro Excel: {e}")
        return []

def main(page: ft.Page):
    # Configurações da Janela/Tela
    page.title = "Exploradores da Bíblia" # MUDANÇA 1: Título da Aba
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#ECF0F1"
    page.scroll = ft.ScrollMode.AUTO
    page.window.width = 450
    page.window.height = 850
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    # MUDANÇA 3: Ícone da Aba (Favicon)
    # Certifique-se de ter um arquivo 'biblia.png' na pasta 'imagens'
    page.favicon = "imagens/biblia.png" 

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

    bd_perguntas = carregar_perguntas(ARQUIVO_PERGUNTAS)
    if not bd_perguntas:
        page.add(ft.Text("ERRO CRÍTICO: Arquivo Excel não encontrado ou inválido.", color="red", size=20))
        return

    # ========================================================================
    #                           TELA 1: CONFIGURAÇÃO
    # ========================================================================

    dd_qtd_participantes = ft.Dropdown(
        label="Nº de Participantes",
        options=[ft.dropdown.Option(str(i)) for i in range(1, 6)],
        value="1", width=150,
        on_change=lambda e: atualizar_campos_nomes()
    )

    col_nomes = ft.Column(spacing=10)

    tf_qtd_perguntas = ft.TextField(label="Qtd. Perguntas", value="6", width=150, keyboard_type=ft.KeyboardType.NUMBER)
    tf_tempo = ft.TextField(label="Tempo (seg)", value="30", width=150, keyboard_type=ft.KeyboardType.NUMBER)

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
            col_nomes.controls.append(
                ft.TextField(label=f"Nome Jogador {i+1}", value=f"Jogador {i+1}", border_color=COR_PRIMARY)
            )
        page.update()

    atualizar_campos_nomes()

    def iniciar_jogo_click(e):
        # Validação
        niveis_sel = []
        if cb_facil.value: niveis_sel.append('FÁCIL')
        if cb_medio.value: niveis_sel.append('MÉDIO')
        if cb_dificil.value: niveis_sel.append('DIFÍCIL')

        if not niveis_sel:
            page.show_snack_bar(ft.SnackBar(ft.Text("Selecione pelo menos um nível!")))
            return

        try:
            qtd_p = int(tf_qtd_perguntas.value)
            tempo = int(tf_tempo.value)
            if tempo < 5: raise ValueError
        except:
            page.show_snack_bar(ft.SnackBar(ft.Text("Verifique quantidade e tempo!")))
            return

        nomes = [campo.value.strip() for campo in col_nomes.controls if campo.value.strip()]
        if not nomes:
            page.show_snack_bar(ft.SnackBar(ft.Text("Preencha os nomes!")))
            return

        # Seleção de Perguntas
        base = [p for p in bd_perguntas if p.get('Nível') in niveis_sel]
        if len(base) < qtd_p: qtd_p = len(base)

        final_perguntas = []
        modo = rg_modo.value

        if modo == "Aleatório":
            final_perguntas = random.sample(base, qtd_p)
            random.shuffle(final_perguntas)
        else: # Progressivo
            p_niveis = {n: [p for p in base if p['Nível'] == n] for n in niveis_sel}
            ordem_niveis = [n for n in ['FÁCIL', 'MÉDIO', 'DIFÍCIL'] if n in niveis_sel]
            
            qtd_niveis = len(ordem_niveis)
            if qtd_niveis > 0:
                base_por_nivel = qtd_p // qtd_niveis
                resto = qtd_p % qtd_niveis
                
                for i, nivel in enumerate(ordem_niveis):
                    qtd_para_este = base_por_nivel + (1 if i < resto else 0)
                    disponiveis = p_niveis[nivel]
                    if disponiveis:
                        selecionadas = random.sample(disponiveis, min(len(disponiveis), qtd_para_este))
                        final_perguntas.extend(selecionadas)

        # Configura Estado
        estado["perguntas_selecionadas"] = final_perguntas
        estado["participantes"] = nomes
        estado["placar"] = {nome: 0 for nome in nomes}
        estado["indice_atual"] = 0
        estado["vez_index"] = 0
        estado["tempo_limite"] = tempo
        estado["modo_jogo"] = modo
        estado["ultimo_nivel_mostrado"] = None
        
        mostrar_tela_resumo()

    btn_iniciar = ft.ElevatedButton("AVANÇAR >>", bgcolor="green", color="white", width=200, height=50, on_click=iniciar_jogo_click)

    view_config = ft.Column(
        [
            # MUDANÇA 2: Imagem de Abertura e Título Ajustado
            ft.Container(
                content=ft.Image(src="imagens/abertura_00.jpg", width=400, height=200, fit=ft.ImageFit.CONTAIN),
                alignment=ft.alignment.center
            ),
            ft.Text("Exploradores da Bíblia", size=28, weight=ft.FontWeight.BOLD, color=COR_PRIMARY, text_align=ft.TextAlign.CENTER),
            ft.Text("Configuração", size=20, weight=ft.FontWeight.BOLD, color="grey", text_align=ft.TextAlign.CENTER),
            
            ft.Divider(),
            ft.Text("Participantes", weight=ft.FontWeight.BOLD),
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
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll=ft.ScrollMode.AUTO
    )

    # ========================================================================
    #                           TELA 1.5: RESUMO
    # ========================================================================

    def mostrar_tela_resumo():
        page.clean()
        
        lista_nomes = ft.Column()
        for nome in estado["participantes"]:
            lista_nomes.controls.append(ft.Text(f"• {nome}", size=18, weight=ft.FontWeight.W_500))

        btn_voltar = ft.OutlinedButton("VOLTAR", width=150, on_click=lambda e: reiniciar_app())
        btn_comecar = ft.ElevatedButton("INICIAR", bgcolor=COR_PRIMARY, color="white", width=150, on_click=lambda e: verificar_transicao_e_iniciar())

        resumo_container = ft.Container(
            content=ft.Column([
                ft.Text("RESUMO DO JOGO", size=25, weight=ft.FontWeight.BOLD, color=COR_PRIMARY),
                ft.Divider(),
                ft.Text("Participantes:", weight=ft.FontWeight.BOLD),
                lista_nomes,
                ft.Divider(),
                ft.Text("Pontuação por Nível:", weight=ft.FontWeight.BOLD),
                ft.Row([ft.Text("Fácil: 5 pts", color="blue")], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([ft.Text("Médio: 10 pts", color="orange")], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([ft.Text("Difícil: 15 pts", color="red")], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(),
                ft.Text(f"Modo: {estado['modo_jogo']}"),
                ft.Text(f"Perguntas: {len(estado['perguntas_selecionadas'])}"),
                ft.Container(height=20),
                ft.Row([btn_voltar, btn_comecar], alignment=ft.MainAxisAlignment.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20,
            bgcolor=COR_CARD,
            border_radius=15,
            width=380,
            shadow=ft.BoxShadow(blur_radius=10, color="#33000000")
        )
        page.add(resumo_container)

    # ========================================================================
    #                           TELA 2: O JOGO
    # ========================================================================

    # Elementos UI Jogo
    txt_vez = ft.Text(value="", size=20, weight=ft.FontWeight.BOLD, color=COR_PRIMARY)
    txt_info_nivel = ft.Text(value="", size=14, color="grey")
    pb_tempo = ft.ProgressBar(width=300, value=1.0, color="green", bgcolor="#eeeeee")
    txt_pergunta = ft.Text(value="", size=20, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
    
    col_opcoes = ft.Column(spacing=10)
    btn_revelar = ft.ElevatedButton("VER OPÇÕES (INICIAR TEMPO)", icon="visibility", bgcolor=COR_SECONDARY, color="white", width=300, height=60)
    
    txt_feedback = ft.Text(value="", size=18, weight=ft.FontWeight.BOLD)
    txt_explicacao = ft.Text(value="", size=16, color="grey", text_align=ft.TextAlign.CENTER)
    
    btn_proxima = ft.ElevatedButton("PRÓXIMA", visible=False)

    def confirmar_saida_jogo(e):
        dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Encerrar Jogo"),
            content=ft.Text("Tem certeza? O jogo terminará e o placar atual será exibido."),
            actions=[
                ft.TextButton("Não", on_click=lambda e: page.close(dlg_modal)),
                ft.TextButton("Sim, Encerrar", on_click=lambda e: encerrar_jogo_imediato(dlg_modal)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dlg_modal)

    def encerrar_jogo_imediato(dlg):
        page.close(dlg) 
        mostrar_placar_final() 

    def mostrar_tela_jogo():
        page.clean()
        
        header_jogo = ft.Row(
            [
                ft.Container(), 
                ft.IconButton(icon="close", icon_color="red", tooltip="Encerrar Jogo", on_click=confirmar_saida_jogo)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        game_container = ft.Container(
            content=ft.Column([
                header_jogo,
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
            padding=10,
            bgcolor=COR_CARD,
            border_radius=20,
            width=380,
            shadow=ft.BoxShadow(blur_radius=10, color="#33000000")
        )
        page.add(game_container)
        preparar_proxima_pergunta()

    def mostrar_tela_transicao(nivel):
        page.clean()
        cor_fundo = CORES_NIVEL.get(nivel, "grey")
        
        def ir_para_jogo(e):
            mostrar_tela_jogo()

        conteudo_transicao = ft.Container(
            content=ft.Column([
                ft.Icon(name="star", color="white", size=80),
                ft.Text(f"NÍVEL {nivel}", size=50, weight=ft.FontWeight.BOLD, color="white"),
                ft.Container(height=50),
                ft.ElevatedButton("CONTINUAR >>", color=cor_fundo, bgcolor="white", width=200, height=60, on_click=ir_para_jogo)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=cor_fundo,
            width=400, height=800, 
            alignment=ft.alignment.center,
            border_radius=20
        )
        page.add(conteudo_transicao)

    def verificar_transicao_e_iniciar():
        if estado["indice_atual"] >= len(estado["perguntas_selecionadas"]):
            mostrar_placar_final()
            return

        prox_pergunta = estado["perguntas_selecionadas"][estado["indice_atual"]]
        novo_nivel = prox_pergunta['Nível']

        deve_mostrar = False
        
        if estado["modo_jogo"] == "Progressivo":
            if estado["indice_atual"] == 0:
                deve_mostrar = True
            elif estado["ultimo_nivel_mostrado"] != novo_nivel:
                deve_mostrar = True
        
        if deve_mostrar:
            estado["ultimo_nivel_mostrado"] = novo_nivel
            mostrar_tela_transicao(novo_nivel)
        else:
            mostrar_tela_jogo()

    def contagem_regressiva():
        tempo_total = estado["tempo_limite"]
        for i in range(tempo_total * 10, -1, -1):
            if not estado["timer_rodando"]: return
            progresso = i / (tempo_total * 10)
            pb_tempo.value = progresso
            if progresso < 0.3: pb_tempo.color = "red"
            else: pb_tempo.color = "green"
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
        nivel = pergunta['Nível']

        nome_jogador = estado["participantes"][estado["vez_index"]]
        txt_vez.value = f"VEZ DE: {nome_jogador.upper()}"
        
        txt_info_nivel.value = f"Pergunta {estado['indice_atual']+1}/{len(estado['perguntas_selecionadas'])} - Nível: {nivel}"
        txt_info_nivel.color = CORES_NIVEL.get(nivel, "black")
        txt_pergunta.value = pergunta['Pergunta']
        
        pontos_map = {'FÁCIL': 5, 'MÉDIO': 10, 'DIFÍCIL': 15}
        estado["pontos_rodada"] = pontos_map.get(nivel, 5)

        col_opcoes.controls.clear()
        col_opcoes.visible = False 
        btn_revelar.visible = True 
        btn_revelar.on_click = lambda e: acao_revelar_opcoes()

        opcoes = [pergunta[f'Opção {L}'] for L in ['A','B','C','D']]
        random.shuffle(opcoes)
        
        for op in opcoes:
            col_opcoes.controls.append(ft.OutlinedButton(
                text=op, width=300, height=50,
                on_click=lambda e, r=op: processar_resposta(r)
            ))

        txt_feedback.value = ""
        txt_explicacao.value = ""
        btn_proxima.visible = False
        pb_tempo.value = 1.0
        
        page.update()

    def acao_revelar_opcoes():
        btn_revelar.visible = False
        col_opcoes.visible = True
        txt_feedback.value = "Selecione a resposta CORRETA!"
        txt_feedback.color = "#00BFFF" 
        page.update()
        
        estado["timer_rodando"] = True
        threading.Thread(target=contagem_regressiva, daemon=True).start()

    def processar_resposta(resposta_usuario, time_out=False):
        estado["timer_rodando"] = False
        pergunta = estado["perguntas_selecionadas"][estado["indice_atual"]]
        correta = pergunta['Resposta Correta']
        
        for btn in col_opcoes.controls:
            btn.disabled = True
            if btn.text == correta:
                btn.style = ft.ButtonStyle(bgcolor="green", color="white")
            elif btn.text == resposta_usuario and not time_out:
                btn.style = ft.ButtonStyle(bgcolor="red", color="white")
        
        if time_out:
            txt_feedback.value = "TEMPO ESGOTADO! ⏰"
            txt_feedback.color = "red"
        elif resposta_usuario == correta:
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
        btn_proxima.on_click = lambda e: avancar_pergunta()
        page.update()

    def avancar_pergunta():
        estado["indice_atual"] += 1
        estado["vez_index"] = (estado["vez_index"] + 1) % len(estado["participantes"])
        verificar_transicao_e_iniciar()

    def mostrar_placar_final():
        page.clean()
        
        ranking = sorted(estado["placar"].items(), key=lambda x: x[1], reverse=True)
        max_score = ranking[0][1] if ranking else 0
        
        lista_ranking = ft.Column()
        for i, (nome, pts) in enumerate(ranking):
            is_champion = (pts == max_score)
            
            cor = "gold" if is_champion else "black"
            size = 30 if is_champion else 18
            weight = ft.FontWeight.BOLD
            
            prefixo = "🏆 " if is_champion else f"{i+1}º "
            
            lista_ranking.controls.append(
                ft.Row([
                    ft.Text(f"{prefixo}{nome}", size=size, color=cor, weight=weight),
                    ft.Text(f"{pts} pts", size=size, color=cor, weight=weight)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            )

        btn_reiniciar = ft.ElevatedButton("NOVO JOGO", bgcolor="blue", color="white", width=200, on_click=lambda e: reiniciar_app())
        btn_sair = ft.ElevatedButton("SAIR DO JOGO", bgcolor="red", color="white", width=200, on_click=lambda e: page.window.close())

        page.add(ft.Container(
            content=ft.Column([
                ft.Text("🏆 FIM DE JOGO 🏆", size=30, weight=ft.FontWeight.BOLD, color=COR_PRIMARY),
                ft.Divider(),
                lista_ranking,
                ft.Divider(),
                btn_reiniciar,
                ft.Container(height=10),
                btn_sair
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=30,
            bgcolor="white",
            border_radius=20
        ))

    def reiniciar_app():
        page.clean()
        page.add(ft.Container(content=view_config, padding=10))

    page.add(ft.Container(content=view_config, padding=10))

# MUDANÇA 4: Configuração para permitir Assets (imagens) e Rodar na Rede
port = int(os.environ.get("PORT", 8080))
ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0")