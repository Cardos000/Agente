
import json
import sys
import os
import time
from main import RealEstateBotMain

MENU = """
============================
 REAL ESTATE BOT - CLI MENU
============================
1. Executar pipeline completo
2. Ver estatísticas rápidas
3. Limpar histórico de vistos
4. Sair
============================
Escolha uma opção: """

def load_json_any_encoding(path):
    encodings = ["utf-8", "utf-8-sig", "latin-1"]
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc) as f:
                return json.load(f)
        except Exception:
            continue
    raise RuntimeError(f"Não foi possível ler {path} em utf-8 nem latin-1.")

def show_stats_menu():
    if not os.path.exists("seen_listings.json"):
        print("Nenhum histórico encontrado.")
        input("\nPressione Enter para voltar ao menu...")
        return
    data = load_json_any_encoding("seen_listings.json")
    while True:
        print("\n==== Estatísticas ====")
        print("1. Resumo geral")
        print("2. Por portal")
        print("3. Por status")
        print("4. Top oportunidades (score)")
        print("5. Voltar ao menu principal")
        op = input("Escolha: ").strip()
        if op == "1":
            print(f"Total de anúncios: {len(data)}")
            aprovados = sum(1 for v in data.values() if v.get("status") == "approved")
            needs_review = sum(1 for v in data.values() if v.get("status") == "needs_review")
            rejeitados = sum(1 for v in data.values() if v.get("status") == "rejected")
            print(f"Aprovados: {aprovados}")
            print(f"Revisão: {needs_review}")
            print(f"Rejeitados: {rejeitados}")
            print(f"Últimos 3 vistos:")
            for k in list(data.keys())[-3:]:
                print(f"- {data[k].get('title', '')[:60]} ({data[k].get('status')})")
            input("\nEnter para continuar...")
        elif op == "2":
            from urllib.parse import urlparse
            portal_stats = {}
            for url, v in data.items():
                netloc = urlparse(url).netloc
                portal = netloc.replace('www.', '').split('.')[0]
                portal_stats.setdefault(portal, 0)
                portal_stats[portal] += 1
            print("\nAnúncios por portal:")
            for portal, count in sorted(portal_stats.items(), key=lambda x: -x[1]):
                print(f"- {portal}: {count}")
            input("\nEnter para continuar...")
        elif op == "3":
            status_stats = {}
            for v in data.values():
                status = v.get("status", "?")
                status_stats.setdefault(status, 0)
                status_stats[status] += 1
            print("\nAnúncios por status:")
            for status, count in sorted(status_stats.items(), key=lambda x: -x[1]):
                print(f"- {status}: {count}")
            input("\nEnter para continuar...")
        elif op == "4":
            scored = [(url, v) for url, v in data.items() if isinstance(v.get("score"), (int, float))]
            top = sorted(scored, key=lambda x: -x[1]["score"])[:10]
            print("\nTop 10 oportunidades:")
            for url, v in top:
                print(f"[{v.get('score', 0)}] {v.get('title', '')[:60]}\n   {url}")
            input("\nEnter para continuar...")
        elif op == "5":
            break
        else:
            print("Opção inválida.")

def clear_history():
    if os.path.exists("seen_listings.json"):
        os.remove("seen_listings.json")
        print("Histórico limpo.")
    else:
        print("Nenhum histórico para limpar.")

def main_cli():
    while True:
        op = input(MENU).strip()
        if op == "1":
            print("A executar pipeline completo...")
            bot = RealEstateBotMain()
            bot.run()
            print("Pipeline concluído.\n")
            time.sleep(1)
        elif op == "2":
            show_stats_menu()
        elif op == "3":
            clear_history()
            input("\nPressione Enter para voltar ao menu...")
        elif op == "4":
            print("A sair...")
            sys.exit(0)
        else:
            print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    main_cli()
