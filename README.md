# pangya-windangle
Reconhecimento do ângulo do vento em screenshots de PangYa (Python3, 2017)

Desenvolvido para uso pessoal como parte da disciplina de Trabalho de Integração 1.
Software que processa uma screenshot de PangYa e retorna o ângulo da seta do vento através de técnicas de processamento de imagens.

Para entender o funcionamento do programa, é recomendável ler o artigo PDF [(pangya-windangle.pdf)](./pangya-windangle.pdf).

![Screenshot original, área relevante realçada em laranja](https://i.imgur.com/gtH9ztX.png)

![Passo 1 - Mudança do espaço de cor e binarização via Otsu](https://i.imgur.com/9cbmBez.png)

![Passo 2-  Aplicação de máscara](https://i.imgur.com/WbwhhfW.png)

![Passo 3 - Suavização do contorno via abertura morfológica](https://i.imgur.com/7DDkj15.png)

![Passo 4 - Obtenção do contorno](https://i.imgur.com/EZCq3s9.png)

![Passo final - Elipse que melhor se ajusta ao contorno. Ângulo = Inclinação da elipse = 3.4 graus](https://i.imgur.com/9rkgWYw.png)