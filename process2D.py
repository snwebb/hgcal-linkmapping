#!/usr/bin/env python3
import pandas as pd
import numpy as np
from rotate import rotate_to_sector_0
import matplotlib.pyplot as plt
import ROOT
import time
import itertools
import random
import sys
from root_numpy import hist2array

np.set_printoptions(threshold=sys.maxsize)
pd.set_option('display.max_rows', None)


infiles = []

def getModuleHists2D(HistFile):

    module_hists = []
    inclusive_hists = []
    
    infiles.append(ROOT.TFile.Open(HistFile,"READ"))

    inclusive = {}
    phi60 = {}
    
    for i in range (15): #u
        for j in range (15): #v
            for k in range (53):#layer
                if ( k < 28 and k%2 == 0 ):
                    continue
                inclusive[0,i,j,k] = infiles[-1].Get("ROverZ_silicon_"+str(i)+"_"+str(j)+"_"+str(k) )
                phi60[0,i,j,k] = inclusive[0,i,j,k].Clone()
                #phi<60 is half the total number of bins in the y-dimension, i.e. for 12 bins (default) would be 6. Set all bins with phi>60 to zero:
                for eta_bin in range(1, 1+phi60[0,i,j,k].GetNbinsX()):
                    for phi_bin in range(1+int(phi60[0,i,j,k].GetNbinsY()/2), 1+phi60[0,i,j,k].GetNbinsY()):
                        phi60[0,i,j,k].SetBinContent(eta_bin,phi_bin,0)
                        phi60[0,i,j,k].SetBinError(eta_bin,phi_bin,0)
                inclusive[0,i,j,k].SetName("ROverZ_silicon_"+str(i)+"_"+str(j)+"_"+str(k) +"_Inclusive")
                phi60[0,i,j,k].SetName("ROverZ_silicon_"+str(i)+"_"+str(j)+"_"+str(k) +"_Phi60")
                
    for i in range (5): #u
        for j in range (12): #v
            for k in range (37,53):#layer
                inclusive[1,i,j,k]= infiles[-1].Get("ROverZ_scintillator_"+str(i)+"_"+str(j)+"_"+str(k) )
                phi60[1,i,j,k] = inclusive[1,i,j,k].Clone()
                #phi<60 is half the total number of bins in the y-dimension, i.e. for 12 bins (default) would be 6. Set all bins with phi>60 to zero:
                for eta_bin in range(1, 1+phi60[1,i,j,k].GetNbinsX()):
                    for phi_bin in range(1+int(phi60[1,i,j,k].GetNbinsY()/2), 1+phi60[1,i,j,k].GetNbinsY()):
                        phi60[1,i,j,k].SetBinContent(eta_bin,phi_bin,0)
                        phi60[1,i,j,k].SetBinError(eta_bin,phi_bin,0)
                inclusive[1,i,j,k].SetName("ROverZ_scintillator_"+str(i)+"_"+str(j)+"_"+str(k) +"_Inclusive")
                phi60[1,i,j,k].SetName("ROverZ_scintillator_"+str(i)+"_"+str(j)+"_"+str(k) +"_Phi60")

    
    PhiVsROverZ = infiles[-1].Get("ROverZ_Inclusive")
    inclusive_hists.append(PhiVsROverZ.ProjectionX( "ROverZ_Inclusive_1D") )
    inclusive_hists.append(PhiVsROverZ.ProjectionX( "ROverZ_Phi60_1D" , 1, 6) )
                
    module_hists.append(inclusive)
    module_hists.append(phi60)
            
    return inclusive_hists,module_hists



def getMiniGroupHists2D(lpgbt_hists, minigroups_swap,root=False):
    
    minigroup_hists = []

    minigroup_hists_inclusive = {}
    minigroup_hists_phi60 = {}
    
    n_binPhi = lpgbt_hists[0][0].GetNbinsY() #get number of bins in phi from one of the hists. 
    phi_120deg = lpgbt_hists[0][0].ProjectionY().GetBinLowEdge(n_binPhi+1) #should be 2.0943951023931953 radian, i.e. 120deg

    for minigroup, lpgbts in minigroups_swap.items():
        
        inclusive = ROOT.TH2D( "minigroup_ROverZ_silicon_" + str(minigroup) + "_0","",42,0.076,0.58,n_binPhi,0.0,phi_120deg) 
        phi60     = ROOT.TH2D( "minigroup_ROverZ_silicon_" + str(minigroup) + "_1","",42,0.076,0.58,n_binPhi,0.0,phi_120deg) 

        for lpgbt in lpgbts:

            inclusive.Add( lpgbt_hists[0][lpgbt] )
            phi60.Add( lpgbt_hists[1][lpgbt] )

            
        inclusive_array = hist2array(inclusive)
        phi60_array = hist2array(phi60) 

        if ( root ):
            minigroup_hists_inclusive[minigroup] = inclusive
            minigroup_hists_phi60[minigroup] = phi60
        else:
            minigroup_hists_inclusive[minigroup] = inclusive_array
            minigroup_hists_phi60[minigroup] = phi60_array
            
    minigroup_hists.append(minigroup_hists_inclusive)
    minigroup_hists.append(minigroup_hists_phi60)

    return minigroup_hists

def getlpGBTHists2D(data, module_hists):

    lpgbt_hists = []
    
    n_binPhi = module_hists[1][0,1,1,1].GetNbinsY() #get bins phi from one of the hists. 
    phi_120deg = module_hists[1][0,1,1,1].ProjectionY().GetBinLowEdge(n_binPhi+1) #should be 2.0943951023931953 radian, i.e. 120deg

    for p,phiselection in enumerate(module_hists):#inclusive and phi < 60

        temp = {}

        for lpgbt in range(0,1600) :
            lpgbt_found = False
            lpgbt_hist = ROOT.TH2D( ("lpgbt_ROverZ_silicon_" + str(lpgbt) + "_" + str(p)),"",42,0.076,0.58,n_binPhi,0.0,phi_120deg);
            
            for tpg_index in ['TPGId1','TPGId2']:#lpgbt may be in the first or second position in the file

                for index, row in (data[data[tpg_index]==lpgbt]).iterrows():  
                    lpgbt_found = True
                    
                    if (row['density']==2):#Scintillator

                        hist = phiselection[ 1, row['u'], row['v'], row['layer'] ] # get module hist
                    else:
                        hist = phiselection[ 0, row['u'], row['v'], row['layer'] ] # get module hist        

                    linkfrac = 'TPGeLinkFrac1'
                    if ( tpg_index == 'TPGId2' ):
                        linkfrac = 'TPGeLinkFrac2'

                    lpgbt_hist.Add( hist, row[linkfrac] ) # add module hist with the correct e-link weight

            if lpgbt_found:
                temp[lpgbt] = lpgbt_hist

        lpgbt_hists.append(temp)
    
    return lpgbt_hists

def getBundledlpgbtHistsRoot2D(minigroup_hists,bundles):

    bundled_lpgbthists = []
    bundled_lpgbthists_list = []

    for p,phiselection in enumerate(minigroup_hists):

        temp = {}

        for i in range(len(bundles)):#loop over bundles

            #Create one lpgbt histogram per bundle
            lpgbt_hist = ROOT.TH1D( ("lpgbt_ROverZ_bundled_" + str(i) + "_" + str(p)),"",42,0.076,0.58);
            
            for minigroup in bundles[i]:#loop over each lpgbt in the bundle
                lpgbt_hist.Add( phiselection[minigroup].ProjectionX())

            temp[i] = lpgbt_hist

        bundled_lpgbthists_list.append(temp)

    return bundled_lpgbthists_list

    
def getBundledlpgbtHists2D(minigroup_hists,bundles):

    #bundled_lpgbthists = [] #not used in the code?
    bundled_lpgbthists_list = []

    for p,phiselection in enumerate(minigroup_hists):

        temp_list = {}

        for i in range(len(bundles)):#loop over bundles

            #Create one lpgbt histogram per bundle
            lpgbt_hist_list = np.zeros(42) 
            
            for minigroup in bundles[i]:#loop over each lpgbt in the bundle
                lpgbt_hist_list+= phiselection[minigroup].sum(axis=1) 

            temp_list[i] = lpgbt_hist_list

        bundled_lpgbthists_list.append(temp_list)

    return bundled_lpgbthists_list

