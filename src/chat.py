from search import search_prompt

def main():
    try:
        chain = search_prompt()
    except Exception as e:
        print(f"Não foi possível iniciar o chat. Erro: {e}")
        print("Verifique se as variáveis de ambiente estão configuradas corretamente.")
        return
    
    print("Bem vindo ao Chat! Digite 'sair' ou 'Ctrl+C' para sair.\n")
    
    while True:
        try:
            question = input("Faça sua pergunta: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ("sair"):
                print("Finalizando o chat...")
                break
            
            print("\nProcessando sua pergunta...")
            response = chain(question)
            
            print(f"\nPERGUNTA: {question}")
            print(f"RESPOSTA: {response}")
            print("---\n")
            
        except KeyboardInterrupt:
            print("\n\Finalizando chat...")
            break
        except Exception as e:
            print(f"\nErro ao processar a tua pergunta: {e}\n")

if __name__ == "__main__":
    main()