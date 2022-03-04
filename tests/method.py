import inspect
import priv

GREEN = "\033[32m"
CYAN = "\033[36m"
RESET = "\033[0m"

class todo:
    def __enter__(self): return
    def __exit__(self, exc_type, exc_value, traceback): 
        if exc_type is not None: print("TODO")
        return True

class MethodAccessM(metaclass=priv.ScopedMeta):
    def met_main(self, *, pself):
        print(CYAN + "met_iv: ", end=RESET)
        self.met_iv()
        print(CYAN + "met_ia: ", end=RESET)
        self.met_ia()
        print(CYAN + "met_pv: ", end=RESET)
        pself.met_pv()
        print(CYAN + "met_pa: ", end=RESET)
        pself.met_pa()
        
        print(CYAN + "cls_iv: ", end=RESET)
        self.cls_iv()
        print(CYAN + "cls_ia: ", end=RESET)
        self.cls_ia()
        print(CYAN + "cls_pv: ", end=RESET)
        pself.cls_pv()
        print(CYAN + "cls_pa: ", end=RESET)
        pself.cls_pa()
        
        print(CYAN + "sta_iv: ", end=RESET)
        self.sta_iv()
        print(CYAN + "sta_ia: ", end=RESET)
        self.sta_ia()
        print(CYAN + "sta_pv: ", end=RESET)
        pself.sta_pv()
        print(CYAN + "sta_pa: ", end=RESET)
        pself.sta_pa()
        
        print(CYAN + "pro_iv: ", end=RESET + "\n")
        self.pro_iv
        self.pro_iv = 0
        del self.pro_iv

        print(CYAN + "pro_ia: ", end=RESET + "\n")
        self.pro_ia
        self.pro_ia = 0
        del self.pro_ia

        print(CYAN + "pro_pv: ", end=RESET + "\n")
        pself.pro_pv
        pself.pro_pv = 0
        del pself.pro_pv

        print(CYAN + "pro_pa: ", end=RESET + "\n")
        pself.pro_pa
        pself.pro_pa = 0
        del pself.pro_pa
        
        print(CYAN + "cpr_iv: ", end=RESET + "\n")
        self.cpr_iv
        self.cpr_iv = 0
        del self.cpr_iv

        print(CYAN + "cpr_ia: ", end=RESET + "\n")
        self.cpr_ia
        self.cpr_ia = 0
        del self.cpr_ia

        print(CYAN + "cpr_pv: ", end=RESET + "\n")
        pself.cpr_pv
        pself.cpr_pv = 0
        del pself.cpr_pv

        print(CYAN + "cpr_pa: ", end=RESET + "\n")
        pself.cpr_pa
        pself.cpr_pa = 0
        del pself.cpr_pa

    @classmethod
    def cls_main(cls, *, pself):
        print(GREEN + "Class access", end=RESET + "\n")
        print(CYAN + "met_iv: ", end=RESET)
        print(cls.met_iv)
        print(CYAN + "met_ia: ", end=RESET)
        print(cls.met_ia)
        print(CYAN + "met_pv: ", end=RESET)
        with todo(): print(pself.met_pv)
        print(CYAN + "met_pa: ", end=RESET)
        with todo(): print(pself.met_pa)
        
        print(CYAN + "cls_iv: ", end=RESET)
        cls.cls_iv()
        print(CYAN + "cls_ia: ", end=RESET)
        cls.cls_ia()
        print(CYAN + "cls_pv: ", end=RESET)
        with todo(): pself.cls_pv()
        print(CYAN + "cls_pa: ", end=RESET)
        with todo(): pself.cls_pa()
        
        print(CYAN + "sta_iv: ", end=RESET)
        cls.sta_iv()
        print(CYAN + "sta_ia: ", end=RESET)
        cls.sta_ia()
        print(CYAN + "sta_pv: ", end=RESET)
        pself.sta_pv()
        print(CYAN + "sta_pa: ", end=RESET)
        pself.sta_pa()
        
        print(CYAN + "pro_iv: ", end=RESET + "\n")
        print(cls.pro_iv, inspect.signature(cls.pro_iv.fget))

        print(CYAN + "pro_ia: ", end=RESET + "\n")
        print(cls.pro_ia, inspect.signature(cls.pro_ia.fget))

        print(CYAN + "pro_pv: ", end=RESET + "\n")
        print(pself.pro_pv, inspect.signature(pself.pro_pv.fget))

        print(CYAN + "pro_pa: ", end=RESET + "\n")
        print(pself.pro_pa, inspect.signature(pself.pro_pa.fget))
        
        print(CYAN + "cpr_iv: ", end=RESET + "\n")
        cls.cpr_iv
        cls.cpr_iv = 0
        del cls.cpr_iv

        print(CYAN + "cpr_ia: ", end=RESET + "\n")
        cls.cpr_ia
        cls.cpr_ia = 0
        del cls.cpr_ia

        print(CYAN + "cpr_pv: ", end=RESET + "\n")
        with todo(): 
            pself.cpr_pv
            pself.cpr_pv = 0
            del pself.cpr_pv

        print(CYAN + "cpr_pa: ", end=RESET + "\n")
        with todo(): 
            pself.cpr_pa
            pself.cpr_pa = 0
            del pself.cpr_pa

    # methods
    def met_iv(self):
        print("public method, var-inaccessible")
    def met_ia(self, *, pself):
        print("public method, var-accessible")
    
    @priv.privatemethod
    def met_pv(self):
        print("private method, var-inaccessible")
    @priv.privatemethod
    def met_pa(self, *, pself):
        print("private method, var-accessible")

    # classmethods
    @classmethod
    def cls_iv(cls):
        print("public classmethod, var-inaccessible", cls)
    @classmethod
    def cls_ia(cls, *, pself):
        print("public classmethod, var-accessible", cls)

    @priv.privatemethod
    @classmethod
    def cls_pv(cls):
        print("private classmethod, var-inaccessible", cls)
    @priv.privatemethod
    @classmethod
    def cls_pa(cls, *, pself):
        print("private classmethod, var-accessible", cls)

    # staticmethod
    @staticmethod
    def sta_iv():
        print("public staticmethod, var-inaccessible")
    @staticmethod
    def sta_ia(*, pself):
        print("public staticmethod, var-accessible")
    
    @priv.privatemethod
    @staticmethod
    def sta_pv():
        print("private staticmethod, var-inaccessible")
    @priv.privatemethod
    @staticmethod
    def sta_pa(*, pself):
        print("private staticmethod, var-accessible")

    # property
    @property
    def pro_iv(self):
        print(self)
        print("public property, var-inaccessible")
    @property
    def pro_ia(self, *, pself):
        print(self)
        print("public property, var-accessible")
    
    @priv.privatemethod
    @property
    def pro_pv(self):
        print(self)
        print("private property, var-inaccessible")
    @priv.privatemethod
    @property
    def pro_pa(self, *, pself):
        print(self)
        print("private property, var-accessible")

    ## property setter
    @pro_iv.setter
    def pro_iv(self, v):
        print("public property setter, var-inaccessible", v)
    @pro_ia.setter
    def pro_ia(self, v, *, pself):
        print("public property setter, var-accessible", v)
    
    @pro_pv.setter
    def pro_pv(self, v):
        print("private property setter, var-inaccessible", v)
    @pro_pa.setter
    def pro_pa(self, v, *, pself):
        print("private property setter, var-accessible", v)

    ## property deleter
    @pro_iv.deleter
    def pro_iv(self):
        print("public property deleter, var-inaccessible")
    @pro_ia.deleter
    def pro_ia(self, *, pself):
        print("public property deleter, var-accessible")
    
    @pro_pv.deleter
    def pro_pv(self):
        print("private property deleter, var-inaccessible")
    @pro_pa.deleter
    def pro_pa(self, *, pself):
        print("private property deleter, var-accessible")

    # class property
    @property
    def cpr_iv(cls):
        print(cls)
        print("public class property, var-inaccessible")
    @property
    def cpr_ia(cls, *, pself):
        print(cls)
        print("public class property, var-accessible")
    
    @property
    def cpr_pv(cls):
        print(cls)
        print("private class property, var-inaccessible")
    @property
    def cpr_pa(cls, *, pself):
        print(cls)
        print("private class property, var-accessible")

    ## class property setter (note that classmethod properties do not support set)
    @cpr_iv.setter
    def cpr_iv(cls, v):
        print("public class property setter, var-inaccessible", v)
    @cpr_ia.setter
    def cpr_ia(cls, v, *, pself):
        print("public class property setter, var-accessible", v)
    
    @cpr_pv.setter
    def cpr_pv(cls, v):
        print("private class property setter, var-inaccessible", v)
    @cpr_pa.setter
    def cpr_pa(cls, v, *, pself):
        print("private class property setter, var-accessible", v)

    ## class property deleter (note that classmethod properties do not support del)
    @classmethod
    @cpr_iv.deleter
    def cpr_iv(cls):
        print("public class property deleter, var-inaccessible")
    @classmethod
    @cpr_ia.deleter
    def cpr_ia(cls, *, pself):
        print("public class property deleter, var-accessible")
    
    @priv.privatemethod
    @classmethod
    @cpr_pv.deleter
    def cpr_pv(cls):
        print("private class property deleter, var-inaccessible")
    @priv.privatemethod
    @classmethod
    @cpr_pa.deleter
    def cpr_pa(cls, *, pself):
        print("private class property deleter, var-accessible")

if __name__ == "__main__":
    ma = MethodAccessM()
    ma.met_main()
    ma.cls_main()