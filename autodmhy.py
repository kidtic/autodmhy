'''
 名称: autodmhy 
 版本: v1.0
 作者: kidtic
 说明: 实现樱花动漫自动追番功能

 环境: 提前设置好代理与比特彗星的远程下载功能
 使用: autodmhy.py会自动遍历当前目录下的所有文件夹，只有文件夹中有dmhyKeyWord.txt的才会被当作工作目录。
       dmhyKeyWord.txt中第一行为樱花动漫的搜索关键字，剩下的为忽略项。
       autodmhy.py会搜索关键字并将搜索的动漫内容下载到当前工作目录（不会下载已经存在的 和 忽略项中的）
 目录结构：
    xxx动漫1/
        xxx01.mp4
        xxx02.mp4
        dmhyKeyWord.txt
    xxx动漫2/
        xxx01.mp4
        xxx02.mp4
        dmhyKeyWord.txt
    autodmhy.py
'''

from requests_html import HTMLSession
import os
from time import sleep


class Search_dmhy:

    curdir = "./"

    list_name = []      #名字
    list_pagelink = []  #网址链接
    list_magnet = []    #磁力链接
    list_filename = []  #文件名称
    list_filesize = []  #文件大小
    keyword = ""        #搜索关键字
    ignlist = []        #忽略

    def __init__(self):
        self.proxie = {"http":"http://127.0.0.1:7890"}  # todo:这里填好代理端口
        url = 'http://www.dmhy.org'  # 这里定义访问的网络地址
        self.url = url
        self.downurl = "http://kk:133z195@192.168.123.205:24564" # todo:这里填好比特彗星的远程下载接口
        self.session = HTMLSession()


    #打开对应的工作空间（包含dmhyKeyWord.txt的文件夹）
    def open(self, dir):
        self.curdir = dir
        #查看当前文件夹下是否有dmhyKeyWord.txt
        tempfname =  os.listdir(dir)
        #print(tempfname)
        if "dmhyKeyWord.txt" not in tempfname: 
            return False
        f = open(dir + "/dmhyKeyWord.txt",'r',encoding='utf-8')
        templst = f.readlines()
        self.keyword = templst[0].replace('\n', '')
        print(self.keyword)
        self.ignlist = templst[1:]
        for i in range(0,len(self.ignlist)):
            self.ignlist[i] = self.ignlist[i].replace('\n', '')
        print(self.ignlist)
        f.close()
       
        return True


    #搜索dmhy网站上相关关键字的结果
    def search(self):
        self.list_name = []
        self.list_pagelink = []
        self.list_magnet = []
        self.list_filename = []
        self.list_filesize = []
        # 打开网页
        mainobj = self.session.get(self.url + "/?keyword=" + self.keyword,proxies=self.proxie)
        # 找到所有的搜索结果
        contents = mainobj.html.find('#topic_list>tbody',first=True).find("tr")

        for tr in contents:
            link = tr.find(".title>a",first=True)
            linkurl = self.url + link.attrs['href']
            self.list_name.append(link.text)
            self.list_pagelink.append(linkurl)

            print(link.text+"   "+ linkurl)
        #查找磁力链接
        for i in range(len(self.list_pagelink)):
            #打开网页
            selobj = self.session.get(self.list_pagelink[i],proxies=self.proxie)

            ####
            magnetStr = selobj.html.find("#a_magnet",first=True).attrs['href']
            templi = selobj.html.find(".file_list",first=True).find("li",first=True)
            tempsize = templi.find("span",first=True)
            namestr = templi.text.replace(tempsize.text,"")
            namestr = namestr.rstrip()
            print(namestr)
            print(tempsize.text)


            self.list_filename.append(namestr)
            self.list_filesize.append(tempsize.text)
            self.list_magnet.append(magnetStr)

        #保存
        f = open(self.curdir+"/index.html", 'w')
        fh_1 = "<html>\n<head></head>\n<body>\n"
        fh_2 = "</body>\n</html>"
        fh_li = ""
        for i in range(len(self.list_magnet)):
            fh_li = fh_li + "<a href=\"%s\">%s</a><span style=\"text-indent:2em\">%s</span><br>\n"%(self.list_magnet[i], self.list_name[i], self.list_filename[i])
        f.write(fh_1)
        f.write(fh_li)
        f.write(fh_2)
        f.close()

    #将不存在工作空间内且不在ignlist内的文件下载到当前目录
    def download(self):
        tempfname =  os.listdir(self.curdir)
        for i in range(len(self.list_filename)):
            if self.list_filename[i] not in tempfname+self.ignlist:
                data={"url":"","save_path":""}
                data["url"] = self.list_magnet[i]
                data["save_path"] = os.path.abspath(".")+"\\"+self.curdir
                print(data["save_path"])
                print(self.list_filename[i])
                self.session.post(self.downurl+"/panel/task_add_magnet_result",data)


    
if __name__ == '__main__':
    dev = Search_dmhy()
    list_allfile = []

    for dirpath, dirnames, filenames in os.walk('.'):
        for dirname in dirnames:  #遍历所有文件夹下的内容
            workpath = os.path.join(dirpath, dirname)
            if dev.open(workpath):  # 查看文件夹下是否有keyword文件
                dev.search()
                dev.download()
