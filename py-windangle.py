# @author Jorge Luiz


# imports
import cv2
import numpy
import glob

# screenshooter imports
import win32gui
import win32ui
import win32con


# globais debug
glob_printstep = False  # print o nome de cada imagem
glob_printresult = False  # mostra os resultados para cada imagem
glob_testmode = False  # usa a base de testes

# variáveis
input_dir = ''
output_dir = 'out/'
avg_error = 0
max_error = 0
img_maxerr = ''
quad_imgs = [0] * 4  # armazena número de imagens por quadrante
quad_err = [0] * 4   # armazena erro total por quadrante


# funções helper para prints
def printstep(string):
    if(glob_printstep):
        print(string)

def printresult(string):
    if(glob_printresult):
        print(string)

def process_img(img_path):
    global avg_error, max_error, img_maxerr

    # abre a imagem e extrai o tamanho dela, extensão e nome do arquivo
    img = cv2.imread(img_path)
    img_name = img_path.split(".")[0]
    img_h, img_w, img_channels = img.shape  # as imagens podem ter diferentes resoluções
    
    # define crop e masks dependendo da resolução (usar apenas na versão Fresh Up?)
    if(img_w == 1024):
        crop_y = img_h - 145
        crop_x = img_w - 131
        size = 108
        mask_img = '_mask1024.png'
        imask_img = '_imask1024.png'
        magic_x = 102
        magic_y = 42

    if(img_w == 640):
        crop_y = img_h - 91
        crop_x = img_w - 83
        size = 68
        mask_img = '_mask640.png'
        imask_img = '_imask640.png'
        magic_x = 64
        magic_y = 26

    # define alguns caminhos importantes - melhor legibilidade no código
    crop_path = output_dir + img_name + '_1_crop.png'
    output_imgpath = output_dir + img_name + "_"

    printstep("processando %s..." % img_name)

    # extrai um quadrado de 68x68 no canto inferior direito - funciona para todas as resoluções
    crop_img = img[crop_y:crop_y+size, crop_x:crop_x+size]
    cv2.imwrite(crop_path, crop_img)

    # aplica máscara
    mask_img = cv2.imread(mask_img, 0)
    proc_img = cv2.bitwise_and(crop_img, crop_img, mask=mask_img)
    color_value = proc_img[magic_y, magic_x]  # ponto para pegar cor para pintar a mask
    proc_img[numpy.where((proc_img==[0,0,0]).all(axis=2))] = color_value
    cv2.imwrite(output_imgpath + "2_mask.png", proc_img)


    # converte para outro espaço de cores
    proc_img = cv2.cvtColor(proc_img, cv2.COLOR_BGR2Lab)
    proc_img = proc_img[:,:,2]  # extrai o canal
    cv2.imwrite(output_imgpath + "3_colorspace.png", proc_img)


    # inpainting
    inmask_img = cv2.imread(imask_img, 0)
    proc_img = cv2.inpaint(proc_img, inmask_img, 1, cv2.INPAINT_NS)
    cv2.imwrite(output_imgpath + "4_inpaint.png", proc_img)


    # normaliza com CLAHE para melhorar o resultado do inpainting
    clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(1,1))
    proc_img = clahe.apply(proc_img)
    cv2.imwrite(output_imgpath + "5_clahe.png", proc_img)


    # binariza a imagem usando otsu
    threshold_value, proc_img = cv2.threshold(proc_img, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    cv2.imwrite(output_imgpath + "6_binary.png", proc_img)


    # aplica morfologia
    kernel = numpy.ones((3,3), numpy.uint8)
    proc_img = cv2.morphologyEx(proc_img, cv2.MORPH_OPEN, kernel, iterations=2)
    cv2.imwrite(output_imgpath + "7_morph.png", proc_img)


    # detecta e desenha o contorno, apenas para fins de visualização
    contours, hierarchy = cv2.findContours(proc_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    contorno_img = cv2.imread(crop_path)
    cv2.drawContours(contorno_img, contours, -1, (0,255,0), 1)
    cv2.imwrite(output_imgpath + "8_contorno.png", contorno_img)


    # desenha a elipse, apenas para fins de visualização
    contours = contours[0]
    ellipse = cv2.fitEllipse(contours)
    cv2.ellipse(crop_img, ellipse, (0,255,0), 1)
    cv2.imwrite(output_imgpath + "9_elipse.png", crop_img)


    # resultado
    printresult("calculando %s..." % img_name)
    ang_obtido = ellipse[2]
    if(ang_obtido > 90):
        ang_obtido = 180 - ang_obtido
    print(ang_obtido)

    # coisas para o test dataset
    if(glob_testmode):
        ang_esperado = int(img_name.split("_")[0])
        ang_esperado /= 10
        error = abs(ang_esperado - ang_obtido)
        printresult("ang esp: %.1f" % ang_esperado)
        printresult("ang obt: %.1f" % ang_obtido)

        printresult("erro: %.1f" % error)
        avg_error += error
        quad_imgs[int(img_name.split("_")[2])-1] += 1
        quad_err[int(img_name.split("_")[2])-1] += error
        if(error > max_error):
            max_error = error
            img_maxerr = img_name

        if(glob_printstep or glob_printresult): # imprime uma newline entre cada iteração do loop se estiver debugando
            print()
# end functions


if(glob_testmode):
    # lista de nomes de arquivos a avaliar
    img_list = glob.glob("*.jpg")
    # print(img_list)

    # loop que trabalha a lista de imagens
    for img_path in img_list:
        process_img(img_path)

    # saída do loop. print dos resultados finais
    print("Analisadas %d imagens... [%d, %d, %d, %d]" % (len(img_list), quad_imgs[0], quad_imgs[1], quad_imgs[2], quad_imgs[3]))

    print("Erro total/médio: %.2f, %.2f" % (avg_error, float(avg_error/len(img_list))))
    print("Erro médio por quadrante: [%.2f], [%.2f], [%.2f], [%.2f]" % (float(quad_err[0]/quad_imgs[0]), float(quad_err[1]/quad_imgs[1]), float(quad_err[2]/quad_imgs[2]), float(quad_err[3]/quad_imgs[3])))
    print("Maior erro: %.1f, %s" % (max_error, img_maxerr))

else:  # olha screenshot em capture
    # pega todas as janelas
    toplist, winlist = [], []
    def enum_cb(hwnd, results):
        winlist.append((hwnd, win32gui.GetWindowText(hwnd)))
    win32gui.EnumWindows(enum_cb, toplist)

    # encontra hwnd do pangya
    pangya = [(hwnd, title) for hwnd, title in winlist if 'pangya fresh up' in title.lower()]
    pangya = pangya[0]
    pangya_hwnd = pangya[0]


    # pega boundaries da janela, calcula dimensões
    l, t, r, b = win32gui.GetWindowRect(pangya_hwnd)
    width = r-l
    height = b-t
    # hardcoding legal para tirar as bordas do windows
    border_size = 8
    top_border = 30
    width -= border_size*2            # direita, esquerda
    height -= top_border+border_size  # top, bottom

    # magic
    hDC = win32gui.GetWindowDC(pangya_hwnd)
    myDC = win32ui.CreateDCFromHandle(hDC)
    newDC = myDC.CreateCompatibleDC()
    
    myBitMap = win32ui.CreateBitmap()
    myBitMap.CreateCompatibleBitmap(myDC, width, height)

    newDC.SelectObject(myBitMap)
    newDC.BitBlt((0,0),(width,height), myDC,(border_size,top_border),win32con.SRCCOPY)
    myBitMap.Paint(newDC)
    myBitMap.SaveBitmapFile(newDC,'10_xd_1.bmp')
    
    process_img('10_xd_1.bmp')
