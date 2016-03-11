import numpy as np
import matplotlib.pyplot as plt
import scipy.signal
import scipy.integrate

class ScopeChannel:
    def __init__(self, shot, scope, channel):
        fn="C:/Users/Sav/Documents/Jack_Caitlin_Sav/scopedata/scope"+scope+"_"+shot
        self.time=np.loadtxt(fn+"time")
        self.data=np.loadtxt(fn+"_"+channel)[1:]
                
class Bdot_pair:
    def __init__(self, shot, scope="1", bdot1='A1', bdot2='A2'):
        self.shot=shot
        #bdot signals 1 and 2
        self.bd1=ScopeChannel(shot, scope, bdot1)
        self.bd2=ScopeChannel(shot, scope, bdot2)
    def truncate(self, threshold=1.0, window=1000, cal=[1,1]):
        #find the start of the current pulse with a  high threshold
        sig1=self.bd1.data
        start=np.nonzero(abs(sig1)>threshold)[0][0]
        #back off a bit so we can see the zero signal
        self.start=start-100
        #reverse the array to find the end of the current pulse with a high threshold
        #end=np.nonzero(abs(sig1[::-1])>threshold)[0][0]
        #back off a bit so we can see the zero signal
        #end=end-100
        #self.end=sig1.size-end #find the index in the non-reversed array
        self.time=self.bd1.time[self.start:self.start+window]
        self.bd1_tr=self.bd1.data[self.start:self.start+window]*cal[0]
        self.bd2_tr=self.bd2.data[self.start:self.start+window]*cal[1]
        self.add()
        self.subtract()
    def add(self):
        self.estat=(self.bd1_tr+self.bd2_tr)/2.0      
    def subtract(self):
        self.dBdt=(self.bd1_tr-self.bd2_tr)/2.0
    def integrate(self):
        self.B=scipy.integrate.cumtrapz(self.dBdt,self.time)/1e9
        self.time_B=self.time[:-1]
    def plot(self, data, ax=None, flip=1, bdname=None):
        if ax is None:
            fig, ax=plt.subplots()
        if bdname is not None:
            b1=bdname[0:2]
            b2=bdname[0]+bdname[2]
        if data is "raw":
            t=self.bd1.time
            d1=self.bd1.data
            d2=self.bd2.data
            l1=b1+' raw'
            l2=b2+' raw'
        if data is "tr":
            t=self.time
            d1=self.bd1_tr
            d2=self.bd2_tr
            l1=b1+' truncated'
            l2=b2+' truncated'
        if data is "sum_diff":
            t=self.time
            d1=self.estat
            d2=self.dBdt
            l1=bdname+' Electrostatic'
            l2=bdname+' dB/dt'
        if data is "B":
            t=self.time_B
            d1=self.B
            d2=None
            l1=bdname+' Magnetic Field'
        ax.plot(t, flip*d1, label=l1, lw=4)
        if d2 is not None:
            ax.plot(t, flip*d2, label=l2, lw=4)
        ax.legend()
        
class Bdots:
    def __init__(self, shot, pairs, attenuations, diameters, scope="1", threshold=1.0):
        self.shot=shot
        self.bd={}
        for k, v in  pairs.items():
            bd1=v+"1"
            bd2=v+"2"
            area=(1e-3*diameters[k]/2.0)**2*np.pi
            calibration=[attenuations[bd1]/area, attenuations[bd2]/area]
            self.bd[k]=Bdot_pair(shot, scope, bdot1=bd1, bdot2=bd2)
            self.bd[k].truncate(threshold=threshold,cal=calibration)
            self.bd[k].integrate()
    def plot(self, name, data, ax=None, flip=1):
        self.bd[name].plot(data, ax, flip, bdname=name)
    def plot_raw(self, name):
        self.bd[name].plot_raw()
    def plot_estat_dBdt(self, name):
        self.bd[name].plot_estat_dBdt()
    def plot_B(self, name):
        self.bd[name].plot_B()
            
            
class Rogowskis:
    def __init__(self, shot):
        self.shot=shot
        #rogowski 1 and 2      
        self.bd1=ScopeChannel(shot, '2', 'c1')
        self.bd2=ScopeChannel(shot, '2', 'c2')
    def truncate(self, threshold=0.5, window=1000, cal=[10*10.4*3e9,-10.48*10.79*3e9]):
    #def truncate(self, threshold=0.2, window=1000, cal=[10*10.4*3e9,-10.48*10.79*3e9]):
        
        #find the start of the current pulse with a  high threshold
        sig1=self.bd1.data
        start=np.nonzero(abs(sig1)>threshold)[0][0]
        #back off a bit so we can see the zero signal
        self.start=start-50
        self.time=self.bd1.time[self.start:self.start+window]
        z1=np.mean(self.bd1.data[0:200]) #zero the data
        z2=np.mean(self.bd2.data[0:200])
        self.bd1_tr=(self.bd1.data[self.start:self.start+window]-z1)*cal[0]
        self.bd2_tr=(self.bd2.data[self.start:self.start+window]-z2)*cal[1]
    def integrate(self, return_posts=8, min_signal=5e4):
        self.I1=scipy.integrate.cumtrapz(self.bd1_tr,self.time)/1e9
        self.I2=scipy.integrate.cumtrapz(self.bd2_tr,self.time)/1e9
        #check currents are positive:
        i1=self.I1
        if np.abs(self.I1.max())<np.abs(self.I1.min()):
            self.I1=-self.I1
        if np.abs(self.I2.max())<np.abs(self.I2.min()):
            self.I2=-self.I2
        #check that tehre's signal
        if self.I2.max()<min_signal:
            self.I_Tot=self.I1*return_posts
            print(self.shot+": using Rog 1 only")
        if self.I1.max()<min_signal:
            self.I_Tot=self.I2*return_posts
            print(self.shot+": using Rog 2 only")
        if self.I1.max()>5e4 and self.I2.max()>5e4:
            self.I_Tot=(self.I1+self.I2)*return_posts/2.0
            print(self.shot+": using both Rogs")
        self.I_Tot1 = self.I1*return_posts
        self.I_Tot2 = self.I2*return_posts
        self.time_I=self.time[:-1]
        t0=self.time_I[np.where(self.I_Tot>2e3)[0][0]]
        self.time_0ed=self.time_I-t0
    def plot(self, data, ax=None, scale=1, bdname=None, plotSep=False):
        if ax is None:
            fig, ax=plt.subplots()
        if data is "raw":
            t=self.bd1.time
            d1=self.bd1.data
            d2=self.bd2.data
            l1='R1 raw'
            l2='R2 raw'
        if data is "tr":
            t=self.time
            d1=self.bd1_tr
            d2=self.bd2_tr
            l1='R1 truncated'
            l2='R2 truncated'
        if data is "I":
            t=self.time_I
            d1=self.I1
            d2=self.I2
            l1='R1 Current'
            l2='R2 Current'
        if data is "I_Tot":
            t=self.time_I
            if plotSep:
                d1=self.I_Tot1
                d2=self.I_Tot2
                l1=self.shot+'current_1'
                l2=self.shot+'current_2'
                print ("Option to plot seperatly was invoked")
            else:
                d1=self.I_Tot    
                d2=None
                l1=self.shot+' Current'
        if data is "I_Tot0":
            t=self.time_0ed
            if plotSep:
                d1=self.I_Tot1
                d2=self.I_Tot2
                print ("Option to plot seperatly was invoked")
                l1=self.shot+'current_1'
                l2=self.shot+'current_2'
            else:
                d1=self.I_Tot
                d2=None
                l1=self.shot+' Current'
        ax.plot(t, scale*d1, label=l1, lw=4)
        if d2 is not None:
            ax.plot(t, scale*d2, label=l2, lw=4)
        ax.legend()