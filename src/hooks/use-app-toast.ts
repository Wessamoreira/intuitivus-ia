import { useToast } from "@/hooks/use-toast";

export const useAppToast = () => {
  const { toast } = useToast();

  const showComingSoon = (feature: string) => {
    toast({
      title: "🚀 Em breve!",
      description: `${feature} está sendo desenvolvido. Inscreva-se na newsletter para ser notificado!`,
    });
  };

  const showSuccess = (message: string) => {
    toast({
      title: "✅ Sucesso!",
      description: message,
    });
  };

  const showDemo = () => {
    toast({
      title: "🎬 Demo Interativo",
      description: "Veja abaixo uma prévia do nosso dashboard inteligente!",
    });
  };

  return { showComingSoon, showSuccess, showDemo };
};