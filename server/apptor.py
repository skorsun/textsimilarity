import random
import os
import glob
import string
import json
import time
import spacy
import logging
import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.autoreload
from tornado import gen
from tornado.options import define, options, parse_command_line
import gensim
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")
MAX_WAIT_SECONDS_BEFORE_SHUTDOWN = 3
MODEL_FOLDER = "models"
NLP = spacy.load('en_core_web_md')
PATH = os.getcwd()
TEXTS_PATH = os.path.join(PATH, 'static', 'texts')
print("TEXTS_PATH", TEXTS_PATH)


def files_list(skip=0, limit=10, ext="txt"):
    files = glob.glob(TEXTS_PATH+"/*."+ext)
    files.sort(key=os.path.getmtime, reverse=True)
    if limit == 0:
        files = files[skip:]
    else:
        files = files[skip:skip+limit]
    return files, len(files)

def get_sentences(idt, sn=-1):
    #  sn == -1  get all sentences from the file
    #   sn = 2    get one sentence
    #   sn = [ 1,3,5] get several sentences
    filename = TEXTS_PATH + "/%s.txt" % idt
    res = None
    if sn == -1:
        res = [s.strip() for s in open(filename, "r", encoding="utf-8", errors='ignore')]
    elif isinstance(sn, list):
        res = [s.strip() for e, s in enumerate(open(filename, "r", encoding="utf-8", errors='ignore')) if e in sn]
    elif isinstance(sn, int) and sn >= 0:
        for e, s in enumerate(open(filename, "r", encoding="utf-8", errors='ignore')):
            if e == sn:
                res = s.strip()
                break
    return res


def randomString(stringLength):
    """Generate a random string with the combination of lowercase and uppercase letters """
    letters = string.ascii_letters
    digits = string.digits
    return ''.join(random.choice(letters)+random.choice(digits) for i in range(stringLength))


def download_file(url, path):
    http = urllib3.PoolManager()
    r = http.request('GET', url, preload_content=False)
    chunk_size = 65536
    with open(path, 'wb') as out:
        while True:
            data = r.read(chunk_size)
            if not data:
                break
            out.write(data)
    r.release_conn()


def sents2vec(content, model, asone=False):
    doc = NLP(content)
    vectors = []
    sentences = []
    all_tokens = []
    for s in doc.sents:
        tks = []
        for t in s:
            if t.text.lower() in model:
                if asone:
                    all_tokens.append(model[t.text.lower()])
                else:
                    tks.append(model[t.text.lower()])
            elif t.text in model:
                if asone:
                    all_tokens.append(model[t.text])
                else:
                    tks.append(model[t.text])
        if not asone:
            vector = np.average(tks, axis=0)
            vectors.append(vector)
            sentences.append(s.string.strip())
    if asone:
        vector = np.average(all_tokens, axis=0)
        vectors.append(vector)
        sentences.append(content)
    vectors = np.array(vectors)
    return sentences, vectors


class BaseHandler(tornado.web.RequestHandler):

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with, content-type")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.set_header('Content-Type', 'application/json')

    @property
    def models(self):
       return self.application.models

    @property
    def vectors(self):
       return self.application.vectors

    @property
    def txtind(self):
       return self.application.txtind

    def options(self):
        # no body
        logging.info("options headers: %s",self.request.headers)
        self.set_status(204)
        self.finish()


class ApiHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        q = self.get_argument("q", "")
        p = self.get_argument("p", "")
        idt = self.get_argument("idt", "")
        sn = self.get_argument("sn", "0")
        print("q", q)
        if sn.isdigit():
            sn = int(sn)
        else:
            sn = 0
        response_object = {'status': 'error'}
        if q == "texts":
            if p.isdigit():
                p = int(p)
            else:
                p = 0
            limit = 10
            skip = p * limit
            compact_text = []
            files, n = files_list(skip, limit)
            for file in files:
                id = os.path.basename(file)[0:-4]
                content = ""
                for line in open(file, "r", encoding="utf-8", errors='ignore'):
                    content += " " + line.strip()
                    if len(content) > 30:
                        content = content[0: 30] + "..."
                        break

                compact_text.append({'id': id, 'content': content})
            response_object['texts'] = compact_text
            rest = n - p * limit
            if rest < 0:
                rest = 0
            response_object['rest'] = rest
            response_object['page'] = p
            response_object["status"] = "success"
            print("response_object", response_object)
        elif q == "sents":
            filename = TEXTS_PATH + "/%s.txt" % idt
            if sn <= 0:
                sents = [s.strip() for s in open(filename, "r", encoding="utf-8", errors='ignore')]
                response_object['texts'] = sents
                response_object['idt'] = idt
                response_object['sn'] = sn
                response_object["status"] = "success"
            else:
                sents = [s.strip() for s in open(filename, "r", encoding="utf-8", errors='ignore')]
                if sn <= len(sents):
                    response_object['texts'] = sents[sn-1]
                    response_object['idt'] = idt
                    response_object['sn'] = sn
                    response_object["status"] = "success"
        elif q == "simsents":
            file_name = TEXTS_PATH + "/" + idt + ".txt"
            snt = ""
            res = []
            if os.path.exists(file_name):
                for i, line in enumerate(open(file_name, "r", encoding="utf-8", errors='ignore')):
                    if i >= sn:
                        snt = line.strip()
                        break
            if snt != "":
                print("snt", snt)
                sent, Xp = sents2vec(snt, self.models["fasttext"], True)
                print("vectors",self.vectors.shape, self.vectors )
                print("Xp",Xp.shape, Xp)
                sim = cosine_similarity(self.vectors, Xp)
                print("sim", sim.shape, sim)
                R = np.argsort(-sim, axis=0)[0:6]
                print("R", R)
                flsn = {}
                flsi = {}
                for i in range(R.shape[0]):
                    j = R[i, 0]
                    if i >= len(self.txtind):
                        continue
                    fn = self.txtind[j][0]
                    flsn.setdefault(fn, [])
                    flsi.setdefault(fn, [])
                    flsn[fn].append(self.txtind[j][1])
                    flsi[fn].append(j)
                res = []
                for k, v in flsn.items():
                    if k == idt and sn in v:
                        v.remove(sn)      # Remove the current sentence from the list of similar sentences
                    sents = get_sentences(k, v)
                    res += zip(sents, flsi[k])
                res = sorted(res, key=lambda x: x[1])
                print(res)
            response_object['texts'] = [s[0] for s in res]
            response_object["status"] = "success"
        print("response_object", response_object)
        self.write(response_object)
        self.finish()

    @gen.coroutine
    def post(self):
        response_object = {"status": "error"}
        try:
            sqs = json.loads(self.request.body.decode(encoding='UTF-8'))
            print(sqs)
            idt = ""
            q = sqs.get("q", "").strip()
            content = sqs.get("content", "").strip()
            if q == "add" and len(content) > 3:
                # Generate and check an unique random id for the text
                while True:
                    idt = randomString(4)
                    file_name = TEXTS_PATH + "/" + idt + ".txt"
                    if not os.path.exists(file_name):
                        break
                # Save the text as list of senteces and calculate vectors for each one
                sentences, vectors = sents2vec(content, self.models["fasttext"], False)
                with open(file_name, "w", encoding="utf8", errors='ignore') as f:
                    for s in sentences:
                        f.write(s + "\n")
                for i in range(vectors.shape[0]):
                    self.txtind.append([idt,i])
                self.vectors = np.vstack((self.vectors, vectors))
                print("vectors",vectors.shape)
                response_object['message'] = 'Text added!'
                response_object['status'] = 'success'
                response_object['id'] = idt
        except Exception as ex:
            logging.exception("api post %s",ex)
        self.write(response_object)
        self.finish()


class ErrorHandler(tornado.web.RequestHandler):
    def get(self,w):
        res = {"result": "error"}
        self.write(res)
        self.finish()


class Application(tornado.web.Application):

    def __init__(self,ioloop):
        self.ioloop = ioloop
        handlers = [
            ( r"/api", ApiHandler),
            (r"/(.*)", ErrorHandler)
            ]
        settings = {
            "debug": True
        }
        tornado.web.Application.__init__(self, handlers, **settings)
        self.models = {}
        mp = "models/wiki-news-300d-1M.vec"
        self.models["fasttext"] = gensim.models.KeyedVectors.load_word2vec_format(mp, binary=False,
                                                                                  limit=50000)
        self.vectors, self.txtind = self.load_vectors()

    def load_vectors(self):
        npy_files, n = files_list(skip=0, limit=0, ext="txt")
        lst = []
        xdata = []
        for file in npy_files:
            id = os.path.basename(file)[0:-4]
            cont = get_sentences(id)
            for i, c in enumerate(cont):
                sent, vec = sents2vec(c, self.models["fasttext"], True)
                xdata.append(vec[0])
                lst.append([id, i])
        X = np.array(xdata, dtype="float32")
        print(X.shape )
        return X, lst


def main():
    parse_command_line()
    ioloop = tornado.ioloop.IOLoop.current()
    http_server = tornado.httpserver.HTTPServer(Application(ioloop))
    http_server.listen(options.port)
    logging.info('Listen port: %s', options.port)
    tornado.ioloop.IOLoop.instance().start()
    logging.info("Exit...")


if __name__ == "__main__":
    main()
