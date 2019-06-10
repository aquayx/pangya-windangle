# @author Jorge Luiz, apoio moral Renan Balbinot
# UTFPR 2017


# imports
import cv2
import numpy
import glob

# globais
glob_printstep = False   # mostra os passos de processamento foram executados para cada imagem
glob_printresult = False  # mostra os resultados para cada imagem

# variáveis
input_dir = ""
output_dir = "out/"
avg_error = 0
max_error = 0
img_maxerr = ""
quad_imgs = [0] * 4  # armazena número de imagens por quadrante
quad_err = [0] * 4   # armazena erro total por quadrante


# funções helper para prints
def printstep(string):
    if(glob_printstep):
        print(string)
        
def printresult(string):
    if(glob_printresult):
        print(string)


# lista de nomes de arquivos a avaliar
img_list = glob.glob("*.jpg")
# print(img_list)
# print()

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
    
    # aplica máscara
    mask_img = cv2.imread('~mask.png', 0)
    proc_img = cv2.bitwise_and(crop_img, crop_img, mask=mask_img)
    color_value = proc_img[26,64]
    proc_img[numpy.where((proc_img==[0,0,0]).all(axis=2))] = color_value
    cv2.imwrite(output_imgpath + "1_mask.png", proc_img)
    printstep("executado passo 1: máscara")
    
    # inpainting
    inmask_img = cv2.imread('~inmask.png', 0)
    proc_img = cv2.inpaint(proc_img, inmask_img, 1, cv2.INPAINT_NS)
    cv2.imwrite(output_imgpath + "2_inpaint.png", proc_img)
    printstep("executado passo 2: inpainting")
    
    # converte para outro espaço de cores
    proc_img = cv2.cvtColor(proc_img, cv2.COLOR_BGR2Lab)
    proc_img = proc_img[:,:,2]  # extrai o canal
    cv2.imwrite(output_imgpath + "3_colorspace.png", proc_img)
    printstep("executado passo 2: conversão para outro espaço de cor")
    
    # inpainting
    inmask_img = cv2.imread('~inmask.png', 0)
    proc_img = cv2.inpaint(proc_img, inmask_img, 1, cv2.INPAINT_NS)
    cv2.imwrite(output_imgpath + "4_inpaint.png", proc_img)
    printstep("executado passo 2: inpainting")
    
    # normaliza com CLAHE para melhorar o resultado do inpainting
    clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(1,1))
    proc_img = clahe.apply(proc_img)
    cv2.imwrite(output_imgpath + "5_dclahe.png", proc_img)
    printstep("executado passo 2: CLAHE")
    
    # binariza a imagem usando otsu
    threshold_value, proc_img = cv2.threshold(proc_img, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    cv2.imwrite(output_imgpath + "6_binary.png", proc_img)
    printstep("executado passo 3: binarização")

    
    # aplica morfologia
    kernel = numpy.ones((3,3), numpy.uint8)
    proc_img = cv2.morphologyEx(proc_img, cv2.MORPH_OPEN, kernel, iterations=2)
    cv2.imwrite(output_imgpath + "7_morph.png", proc_img)
    printstep("executado passo 5: abertura")
    
    # detecta contorno
    contours, hierarchy = cv2.findContours(proc_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    # desenha o contorno, apenas para fins de visualização
    contorno_img = cv2.imread(crop_path)
    cv2.drawContours(contorno_img, contours, -1, (0,255,0), 1)
    cv2.imwrite(output_imgpath + "8_contorno.png", contorno_img)
    printstep("executado passo 6: detectado contorno")
    
    
    # desenha a elipse
    contours = contours[0]
    ellipse = cv2.fitEllipse(contours)
    # desenha a elipse, apenas para fins de visualização
    cv2.ellipse(crop_img, ellipse, (0,255,0), 1)
    cv2.imwrite(output_imgpath + "9_elipse.png", crop_img)
    printstep("executado passo 7: traçada elipse")


    # análise dos resultados
    printresult("calculando %s..." % img_name)
    ang_obtido = ellipse[2]
    if(ang_obtido > 90):
        ang_obtido = 180 - ang_obtido

    # ang_esperado apenas deve ser usado para as imagens de debugging
    ang_esperado = int(img_name.split("_")[0])
    ang_esperado /= 10
    error = abs(ang_esperado - ang_obtido)
    printresult("ang esp: %.1f" % ang_esperado)
    printresult("ang obt: %.1f" % ang_obtido)

    # mais lógica de debugging
    printresult("erro: %.1f" % error)
    avg_error += error
    quad_imgs[int(img_name.split("_")[2])-1] += 1
    quad_err[int(img_name.split("_")[2])-1] += error
    if(error > max_error):
        max_error = error
        img_maxerr = img_name

    if(glob_printstep or glob_printresult): # imprime uma newline entre cada iteração do loop se estiver debugando
        print()


# saída do loop. print dos resultados finais
print("Analisadas %d imagens... [%d, %d, %d, %d]" % (len(img_list), quad_imgs[0], quad_imgs[1], quad_imgs[2], quad_imgs[3]))

print("Erro total/médio: %.2f, %.2f" % (avg_error, float(avg_error/len(img_list))))
print("Erro médio por quadrante: [%.2f], [%.2f], [%.2f], [%.2f]" % (float(quad_err[0]/quad_imgs[0]), float(quad_err[1]/quad_imgs[1]), float(quad_err[2]/quad_imgs[2]), float(quad_err[3]/quad_imgs[3])))
print("Maior erro: %.1f, %s" % (max_error, img_maxerr))
