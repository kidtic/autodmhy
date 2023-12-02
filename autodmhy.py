'''
 名称: autodmhy 
 版本: v1.4
 作者: kidtic
 说明: 实现动漫花园www.dmhy.org自动追番功能

 环境: 提前设置好代理与比特彗星的远程下载功能
 使用: autodmhy.py会自动遍历当前目录下的所有文件夹，只有文件夹中有dmhy.json的才会被当作工作目录。
        终端运行 【autodmhy.py add "关键词"】 会添加指定的目录
        终端运行 【autodmhy.py ref】会重新刷新所有的dmhy.json的items，同步网站内容。
        终端运行 【autodmhy.py】 动态更新items，并且进行自动补充下载
 目录结构：
    xxx动漫1/
        xxx01.mp4
        xxx02.mp4
        dmhy.json
    xxx动漫2/
        xxx01.mp4
        xxx02.mp4
        dmhy.json
    autodmhy.py

 版本改动: 
    v1.1 - 将所有正在追番的目录打印出来，并且停在最后。
    v1.2 - 取消代理
    v1.3 - 修改框架 dmhy.json
    v1.4 - 加入重命名功能，不过需要把比特彗星的任务停掉重新运行才行。
'''

from requests_html import HTMLSession
import os
from time import sleep
import json
import re
import sys

def find_common_substrings(strings):
    min_str = min(strings, key=len)
    substrings = []
    length = len(min_str)
    while length > 0:
        for i in range(len(min_str) - length + 1):
            substr = min_str[i:i+length]
            if all(substr in s for s in strings):
                substrings.append(substr)
        length -= 1
    substrings = [s for s in substrings if not any(s != t and s in t for t in substrings)]
    return substrings

def first_num(s):
    # 使用正则表达式寻找1位或2位的数字
    match = re.search(r'\d{1,2}', s)
    # 如果找到匹配项，返回该数字，否则返回None
    return int(match.group()) if match else None

def autoReName_mp4(titlename,videofile):
    '''
    智能重命名 return [src][dst]
    '''
    result = find_common_substrings(videofile)
    strings_list = []
    for estr in videofile:
        vidname = estr
        houzhui = ".mp4"
        if vidname.endswith(".mkv"):
            houzhui = ".mkv"
        elif vidname.endswith(".mp4"):
            houzhui = ".mp4"
        
        for spe in result:
            estr = estr.replace(spe,"")
        #找到头个位数字
        print(estr)
        tnum = first_num(estr)
        if tnum is None:
            strings_list.append([vidname,""])
        else:
            strnum = "{:02d}".format(tnum)
            print(strnum)
            instr = titlename+" E"+strnum+houzhui
            strings_list.append([vidname,instr])
    #重复名字将不会重新命名
    strset = []
    for i in range(len(strings_list)):
        if strings_list[i][1] in strset:
            strings_list[i][1] = strings_list[i][0]
        elif strings_list[i][1]=="":
            strings_list[i][1] = strings_list[i][0]
        else:
            strset.append(strings_list[i][1])
    return strings_list


class Search_dmhy:

    curdir = "./"

    list_name = []      #名字
    list_pagelink = []  #网址链接
    list_magnet = []    #磁力链接
    list_filename = []  #文件名称
    list_filesize = []  #文件大小
    keyword = ""        #搜索关键字
    ignlist = []        #忽略
    dmhyjson = None
    dmname = None
    season = ""

    def __init__(self):
        #self.proxie = {"http":"http://127.0.0.1:7890"}  # todo:这里填好代理端口
        self.proxie = None
        url = 'http://www.dmhy.org'  # 这里定义访问的网络地址
        self.url = url
        self.downurl = "http://kk:133z195@localhost:24564" # todo:这里填好比特彗星的远程下载接口
        self.session = HTMLSession()

    def findweb(self,url):
        '''
        解析动漫花园资源帖子网站内容
        '''
        try:
            #打开网页
            selobj = self.session.get(url,proxies=self.proxie)
            ####
            magnetStr = selobj.html.find("#a_magnet",first=True).attrs['href']
            templi = selobj.html.find(".file_list",first=True).find("li",first=True)
            tempsize = templi.find("span",first=True)
            namestr = templi.text.replace(tempsize.text,"")
            namestr = namestr.rstrip()
            print(namestr)
            print(tempsize.text)
            item = {"magnet":magnetStr, "file":namestr, "filesize":tempsize.text}
            return item
        except:
            return None

    def open(self, dir):
        '''
        打开对应的工作空间（包含dmhy.json的文件夹）
        '''
        self.curdir = dir
        #查看当前文件夹下是否有dmhy.json
        tempfname =  os.listdir(dir)
        #print(tempfname)
        if "dmhy.json" not in tempfname: 
            return False
        with open(dir + "/dmhy.json",'r',encoding='utf-8') as f:
            self.dmhyjson =json.load(f)
            self.keyword = self.dmhyjson["keyword"]
            print(self.keyword)
            self.ignlist = self.dmhyjson["ignlist"]
            print(self.ignlist)
            self.dmname = self.dmhyjson["name"]
            self.season = self.dmhyjson["season"]
            if self.keyword is None:
                return False
            if self.dmname is None:
                return False

        return True
    

    def rename(self):
        '''
        将依据dmhy.json中的内容、以及当前目录下显示存在的文件为依据 重新命名
        '''
        jsonitems = self.dmhyjson["items"]
        if len(jsonitems)<2:return
        #按照items里面原本的视频名称列表来自动生成一组
        srcfname_list=[]
        for e in jsonitems:
            srcfname_list.append(e["file"])
        titlename = self.dmname +" "+self.season
        rename_list = autoReName_mp4(titlename,srcfname_list)
        #列出当前文件夹下所有文件
        dirFileList =  os.listdir(self.curdir)

        for i in range(len(srcfname_list)):
            srcfile = rename_list[i][0]
            dstfile = rename_list[i][1]
            currRname = ""
            try:
                currRname = jsonitems[i]["rename"]  #获取当前的原始文件的重命名文件，用于查找
            except:
                currRname = ""
            existFile = ""      #当前文件中存在的与之匹配的文件
            if currRname in dirFileList:
                existFile = currRname
            elif srcfile in dirFileList:
                existFile = srcfile
            
            if existFile=="":continue
            #重新命名
            print("rename:  "+dstfile+"  <=  "+existFile)
            os.rename(self.curdir+"/"+existFile,self.curdir+"/"+dstfile)
            #重写item
            jsonitems[i].update({"rename":dstfile})
        self.dmhyjson["items"] = jsonitems

    def search(self,fetch=False):
        '''
        搜索dmhy网站上相关关键字的结果 

        ``fetch`` 代表强制刷新items，会遍历所有网址
        '''
        self.list_name = []         #网页标题
        self.list_pagelink = []     #网页地址
        self.list_magnet = []
        self.list_filename = []
        self.list_filesize = []
        if self.keyword is None:return
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

        if fetch:
            items = []
            #查找磁力链接
            for i in range(len(self.list_pagelink)):
                item = self.findweb(self.list_pagelink[i])
                if item is None:
                    print("网站解析异常，跳过")
                    continue
                item["webtitle"] = self.list_name[i]
                items.append(item)
            #重写item
            self.dmhyjson["items"] = items
        else:
            #先判断dmhy.json的items里有没有项目
            items = self.dmhyjson["items"]
            #将dmhyjson中items选项的webtitle汇集一下
            items_titles = []
            for e in items:
                items_titles.append(e["webtitle"])
            #查看list_name中多出来了多少项目
            for i in range(len(self.list_name)):
                title = self.list_name[i]
                if title in items_titles:continue
                #打开网页查找磁力
                item = self.findweb(self.list_pagelink[i])
                #加入items
                item["webtitle"] = title
                items.append(item)
            #重写item
            self.dmhyjson["items"] = items
            #智能重新命名
            self.rename()
        #将self.dmhyjson存入
        with open(self.curdir + "/dmhy.json",'w',encoding='utf-8') as f:
            json.dump(self.dmhyjson, f, indent=4, ensure_ascii=False)


    def download(self):
        '''
        将不存在工作空间内且不在ignlist内的文件下载到当前目录
        '''
        #检查dmhyjson的items有没有存在在这个目录的
        tempfname =  os.listdir(self.curdir)
        items_files = []
        items_renamef = []
        items_magnet = []
        for e in self.dmhyjson["items"]:
            items_files.append(e["file"])
            items_magnet.append(e["magnet"])
            items_renamef.append(e["rename"])

        for i in range(len(items_files)):
            if items_files[i] in tempfname+self.ignlist:continue
            if items_renamef[i] in tempfname+self.ignlist:continue
            data={"url":"","save_path":""}
            data["url"] = items_magnet[i]
            data["save_path"] = os.path.abspath(".")+"\\"+self.curdir
            print(data["save_path"])
            print(items_files[i])
            self.session.post(self.downurl+"/panel/task_add_magnet_result",data)
    
if __name__ == '__main__':
    dev = Search_dmhy()
    list_allfile = []

    for dirpath, dirnames, filenames in os.walk('.'):
        for dirname in dirnames:  #遍历所有文件夹下的内容
            workpath = os.path.join(dirpath, dirname)
            if dev.open(workpath):  # 查看文件夹下是否有keyword文件
                list_allfile.append(workpath)
                dev.search()
                dev.download()
    #print res
    print("====================目前追番列表===================")
    for e in list_allfile:
        print(e)
    
    input("Press any key to continue")