"""
OpenAI Handler Module
Integra com OpenAI para gerar respostas inteligentes
"""

from openai import OpenAI
from dotenv import load_dotenv
import os
from typing import Dict, Optional
from client_identifier import ClientIdentifier

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class OpenAIHandler:
    """Gerencia interações com OpenAI"""
    
    def __init__(self):
        self.client = client
        self.identifier = ClientIdentifier()
        self.model = "gpt-4.1-mini"
        self.temperature = 0.7
        self.max_tokens = 500
    
    def generate_response(
        self,
        user_message: str,
        conversation_context: str,
        client_type_prompt: str,
        phone: Optional[str] = None
    ) -> Dict:
        """
        Gera resposta inteligente usando OpenAI
        
        Args:
            user_message: Mensagem do usuário
            conversation_context: Contexto da conversa
            client_type_prompt: Prompt personalizado para tipo de cliente
            phone: Número do WhatsApp (opcional)
            
        Returns:
            Dict com resposta gerada
        """
        try:
            # Constrói o prompt do sistema
            system_prompt = f"""{client_type_prompt}

## Contexto da Conversa:
{conversation_context}

## Instruções Importantes:
1. Responda SEMPRE em português brasileiro
2. Mantenha a conversa natural e amigável
3. Seja conciso (máximo 2-3 linhas)
4. Não repita informações já ditas
5. Faça perguntas para qualificar o lead
6. Ofereça próximos passos claros
7. Nunca peça informações desnecessárias
8. Respeite o tom e contexto da conversa anterior"""
            
            # Faz a chamada à OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            generated_text = response.choices[0].message.content
            
            return {
                "success": True,
                "response": generated_text,
                "phone": phone,
                "tokens_used": response.usage.total_tokens,
                "model": self.model
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "Desculpe, não consegui processar sua mensagem. Tente novamente.",
                "phone": phone
            }
    
    def generate_prospecting_message(
        self,
        client_type_prompt: str,
        conversation_context: str = "",
        phone: Optional[str] = None
    ) -> Dict:
        """
        Gera mensagem de prospecção inicial
        
        Args:
            client_type_prompt: Prompt personalizado
            conversation_context: Contexto anterior (se houver)
            phone: Número do WhatsApp
            
        Returns:
            Dict com mensagem gerada
        """
        try:
            system_prompt = f"""{client_type_prompt}

## Tarefa:
Gere uma mensagem de prospecção INICIAL para este cliente.
A mensagem deve ser:
1. Personalizada para o tipo de cliente
2. Curta (máximo 3 linhas)
3. Com uma pergunta ou call-to-action claro
4. Profissional mas amigável
5. Em português brasileiro

Não inclua saudações genéricas. Vá direto ao ponto."""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Gere a mensagem de prospecção"}
                ],
                temperature=0.8,
                max_tokens=300
            )
            
            message = response.choices[0].message.content
            
            return {
                "success": True,
                "message": message,
                "phone": phone,
                "type": "prospecting"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "phone": phone
            }
    
    def generate_followup_message(
        self,
        client_type_prompt: str,
        conversation_context: str,
        phone: Optional[str] = None
    ) -> Dict:
        """
        Gera mensagem de follow-up (reenvio após 24h)
        
        Args:
            client_type_prompt: Prompt personalizado
            conversation_context: Contexto da conversa
            phone: Número do WhatsApp
            
        Returns:
            Dict com mensagem gerada
        """
        try:
            system_prompt = f"""{client_type_prompt}

## Tarefa:
Gere uma mensagem de FOLLOW-UP para este cliente que não respondeu.
A mensagem deve ser:
1. Leve e não invasiva
2. Curta (máximo 2 linhas)
3. Referenciar a conversa anterior
4. Oferecer valor ou próximo passo
5. Em português brasileiro

Exemplo: "Oi! Só queria confirmar se você recebeu minha mensagem anterior. Fico à disposição!"
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Contexto: {conversation_context}\n\nGere a mensagem de follow-up"}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            message = response.choices[0].message.content
            
            return {
                "success": True,
                "message": message,
                "phone": phone,
                "type": "followup"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "phone": phone
            }
    
    def analyze_client_response(
        self,
        client_response: str,
        client_type_prompt: str
    ) -> Dict:
        """
        Analisa resposta do cliente para determinar próximo passo
        
        Args:
            client_response: Resposta do cliente
            client_type_prompt: Prompt personalizado
            
        Returns:
            Dict com análise
        """
        try:
            system_prompt = f"""{client_type_prompt}

## Tarefa:
Analise a resposta do cliente e determine:
1. Nível de interesse (alto, médio, baixo)
2. Próximo passo recomendado
3. Objeções identificadas
4. Dados importantes mencionados

Retorne em formato JSON com as chaves:
- interest_level
- next_step
- objections
- important_data
- recommendation"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Resposta do cliente: {client_response}"}
                ],
                temperature=0.5,
                max_tokens=400
            )
            
            analysis_text = response.choices[0].message.content
            
            return {
                "success": True,
                "analysis": analysis_text
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_smart_response(
        self,
        user_message: str,
        phone: str,
        conversation_context: str
    ) -> Dict:
        """
        Gera resposta inteligente com identificação automática de tipo de cliente
        
        Args:
            user_message: Mensagem do usuário
            phone: Número do WhatsApp
            conversation_context: Contexto da conversa
            
        Returns:
            Dict com resposta gerada
        """
        # Identifica tipo de cliente
        client_type, confidence = self.identifier.identify_client_type(conversation_context)
        client_prompt = self.identifier.get_prompt_for_client(client_type)
        
        # Gera resposta
        response = self.generate_response(
            user_message=user_message,
            conversation_context=conversation_context,
            client_type_prompt=client_prompt,
            phone=phone
        )
        
        # Adiciona informações de identificação
        response["client_type"] = client_type.value
        response["client_confidence"] = confidence
        
        return response


# Exemplo de uso
if __name__ == "__main__":
    handler = OpenAIHandler()
    
    # Teste 1: Resposta para síndico
    print("=== Teste 1: Síndico ===")
    context = """
    Cliente: Oi, sou síndico do condomínio Flores com 50 apartamentos
    Agente: Ótimo! Trabalho com síndicos para reduzir custos de energia
    Cliente: Qual é o valor da auditoria?
    """
    
    response = handler.generate_response(
        user_message="Qual é o valor da auditoria?",
        conversation_context=context,
        client_type_prompt=handler.identifier.get_prompt_for_client(
            handler.identifier.identify_client_type(context)[0]
        ),
        phone="5585987654321"
    )
    
    print(f"Resposta: {response['response']}")
    
    # Teste 2: Mensagem de prospecção
    print("\n=== Teste 2: Mensagem de Prospecção ===")
    prospect_response = handler.generate_prospecting_message(
        client_type_prompt=handler.identifier.prompts[handler.identifier.ClientType.FARM],
        phone="5585987654321"
    )
    
    print(f"Mensagem: {prospect_response['message']}")
