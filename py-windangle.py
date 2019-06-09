# @author Jorge Luiz, apoio moral Renan Balbinot
# UTFPR 2017


# imports
import cv2
import numpy as np
import glob

# globais
glob_printstep = False    # mostra os passos de processamento foram executados para cada imagem
glob_printresult = True  # mostra os resultados para cada imagem

# variáveis
input_dir = ""
output_dir = "out/"
avg_error = 0
max_error = 0


# funções helper para prints
def printstep(string):
    if(glob_printstep):
        print(string)
        
def printresult(string):
    if(glob_printresult):
        print(string)


# lista de nomes de arquivos a avaliar
img_list = glob.glob("*.jpg")
print(img_list)
print()

# loop que trabalha a lista de imagens
for img_path in img_list:

    # abre a imagem e extrai o tamanho dela, extensão e nome do arquivo
    img = cv2.imread(img_path)
    img_name = img_path.split(".")[0]
    img_h, img_w, img_channels = img.shape  # as imagens podem ter diferentes resoluções
    
    # define alguns caminhos importantes - melhor legibilidade no código
    crop_path = output_dir + img_name + "_1_crop.png"
    output_imgpath = output_dir + img_name + "_"
    
    printstep("processando %s..." % img_name)
    
    # extrai um quadrado de 68x68 no canto inferior direito - funciona para todas as resoluções
    crop_img = img[img_h-91:img_h-91+68, img_w-83:img_w-83+68]
    cv2.imwrite(crop_path, crop_img)
    printstep("executado passo 1: crop")


    # converte para outro espaço de cores
    colorspace_img = cv2.cvtColor(crop_img, cv2.COLOR_BGR2Lab)
    colorspace_img = colorspace_img[:,:,2]  # extrai o canal
    cv2.imwrite(output_imgpath + "2_colorspace.png", colorspace_img)
    printstep("executado passo 2: conversão para outro espaço de cor")

    # teste inpainting
    inmask_img = cv2.imread('~inmask.png', 0)
    colorspace_img = cv2.inpaint(colorspace_img, inmask_img, 2, cv2.INPAINT_NS)
    cv2.imwrite(output_imgpath + "2_inpaint.png", colorspace_img)
    printstep("executado passo 6: inpainting")
    
    # binariza a imagem usando otsu
    threshold_value, binary_img = cv2.threshold(colorspace_img, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    cv2.imwrite(output_imgpath + "3_binary.png", binary_img)
    printstep("executado passo 3: binarização")
    
    
    # aplica máscara
    mask_img = cv2.imread('~mask.png', 0)
    mask_img = cv2.bitwise_and(binary_img, binary_img, mask=mask_img)
    cv2.imwrite(output_imgpath + "4_mask.png", mask_img)
    printstep("executado passo 4: máscara")
    
    
    # aplica morfologia
    kernel = np.ones((3,3), np.uint8)
    morph_img = cv2.morphologyEx(mask_img, cv2.MORPH_OPEN, kernel, iterations=2)
    cv2.imwrite(output_imgpath + "5_morph.png", morph_img)
    printstep("executado passo 5: abertura")
    
    '''
    # teste inpainting
    inmask_img = cv2.imread('~inmask.png', 0)
    morph_img = cv2.inpaint(morph_img, inmask_img, 2, cv2.INPAINT_NS)
    cv2.imwrite(output_imgpath + "6_inpaint.png", morph_img)
    printstep("executado passo 6: inpainting")
    '''

    # detecta contorno
    contours, hierarchy = cv2.findContours(morph_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    # desenha o contorno, apenas para fins de visualização
    contorno_img = cv2.imread(crop_path)
    cv2.drawContours(contorno_img, contours, -1, (0,255,0), 1)
    cv2.imwrite(output_imgpath + "6_contorno.png", contorno_img)
    printstep("executado passo 6: detectado contorno")
    
    
    # desenha a elipse
    contours = contours[0]
    ellipse = cv2.fitEllipse(contours)
    # desenha a elipse, apenas para fins de visualização
    cv2.ellipse(crop_img,ellipse,(0,255,0),1)
    cv2.imwrite(output_imgpath + "7_elipse.png", crop_img)
    printstep("executado passo 7: traçada elipse")
    
    
    # análise dos resultados
    printresult("calculando %s..." % img_name)
    ang_obtido = ellipse[2]
    if(ang_obtido > 90):
        ang_obtido = 180 - ang_obtido
    
    # ang_esperado apenas deve ser usado para as imagens de debugging
    ang_esperado = int(img_name.split("_")[1])
    ang_esperado /= 10
    error = abs(ang_esperado - ang_obtido)
    printresult("ang esp: %.1f" % ang_esperado)
    printresult("ang obt: %.1f" % ang_obtido)
    
    # mais lógica de debugging
    printresult("erro: %.1f" % error)
    avg_error += error
    if(error > max_error):
        max_error = error
    
    if(glob_printstep or glob_printresult): # imprime uma newline entre cada iteração do loop se estiver debugando
        print()
    

# saída do loop. print dos resultados finais
print("Analisadas %d imagens..." % len(img_list))
print("Erro médio: %.1f" % float(avg_error/len(img_list)))
print("Maior erro: %.1f" % max_error)