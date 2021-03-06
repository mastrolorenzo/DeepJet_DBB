'''
Created on 21 Feb 2017

@author: jkiesele
'''

from TrainData import TrainData, fileTimeOut
from TrainData import TrainData_simpleTruth
import numpy

class TrainData_deepCSV_PF_Reg(TrainData_simpleTruth):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        TrainData.__init__(self)
        
        
        self.addBranches(['jet_pt', 'jet_eta','nCpfcand','nNpfcand','nsv','npv'])
       
        self.addBranches(['Cpfcan_BtagPf_trackEtaRel',
                          'Cpfcan_BtagPf_trackPtRel',
                          'Cpfcan_BtagPf_trackDeltaR',
                          'Cpfcan_BtagPf_trackPtRatio',
                          'Cpfcan_BtagPf_trackSip2dSig',
                          'Cpfcan_BtagPf_trackSip3dSig',
                          'Cpfcan_BtagPf_trackJetDistVal',
                          
                          'Cpfcan_BtagPf_trackJetDistSig',
                          
                          'Cpfcan_erel',
                          'Cpfcan_drminsv',
                          'Cpfcan_chi2',
                          'Cpfcan_fromPV',
                          'Cpfcan_VTX_ass',
                          
                          #new
                          #'Cpfcan_puppiw'
                              ],
                             20)
        
        
        self.addBranches(['Npfcan_erel',
                          'Npfcan_deltaR',
                              'Npfcan_isGamma',
                              'Npfcan_HadFrac',
                              'Npfcan_drminsv',
                              ],
                             15)
        
        
        self.addBranches(['sv_pt',
                              'sv_etarel',
                              'sv_phirel',
                              'sv_deltaR',
                              'sv_mass',
                              'sv_ntracks',
                              'sv_chi2',
                              'sv_ndf',
                              'sv_normchi2',
                              'sv_dxy',
                              'sv_dxyerr',
                              'sv_dxysig',
                              'sv_d3d',
                              'sv_d3derr',
                              'sv_d3dsig',
                              'sv_costhetasvpv',
                              'sv_enratio',
                              ],
                             4)

    
        
        self.regtruth='gen_pt_WithNu'
        self.regreco='jet_corr_pt'
        
        self.registerBranches([self.regtruth,self.regreco])
        
       
    def readFromRootFile(self,filename,TupleMeanStd, weighter):
        from preprocessing import MeanNormApply, MeanNormZeroPad, MeanNormZeroPadParticles
        import numpy
        from stopwatch import stopwatch
        
        sw=stopwatch()
        swall=stopwatch()
        
        import ROOT
        
        fileTimeOut(filename,120) #give eos a minute to recover
        rfile = ROOT.TFile(filename)
        tree = rfile.Get("deepntuplizer/tree")
        self.nsamples=tree.GetEntries()
        
        print('took ', sw.getAndReset(), ' seconds for getting tree entries')
        
        
        # split for convolutional network
        
        x_global = MeanNormZeroPad(filename,TupleMeanStd,
                                   [self.branches[0]],
                                   [self.branchcutoffs[0]],self.nsamples)
        
        x_cpf = MeanNormZeroPadParticles(filename,TupleMeanStd,
                                   self.branches[1],
                                   self.branchcutoffs[1],self.nsamples)
        
        x_npf = MeanNormZeroPadParticles(filename,TupleMeanStd,
                                   self.branches[2],
                                   self.branchcutoffs[2],self.nsamples)
        
        x_sv = MeanNormZeroPadParticles(filename,TupleMeanStd,
                                   self.branches[3],
                                   self.branchcutoffs[3],self.nsamples)
        
        
        
        print('took ', sw.getAndReset(), ' seconds for mean norm and zero padding (C module)')
        
        Tuple = self.readTreeFromRootToTuple(filename)
        
        if self.remove:
            notremoves=weighter.createNotRemoveIndices(Tuple)
            undef=Tuple['isUndefined']
            notremoves-=undef
            print('took ', sw.getAndReset(), ' to create remove indices')
        
        if self.weight:
            weights=weighter.getJetWeights(Tuple)
        elif self.remove:
            weights=notremoves
        else:
            print('neither remove nor weight')
            weights=numpy.empty(self.nsamples)
            weights.fill(1.)
        
        pttruth=Tuple[self.regtruth]
        ptreco=Tuple[self.regreco]
        
        truthtuple =  Tuple[self.truthclasses]
        #print(self.truthclasses)
        alltruth=self.reduceTruth(truthtuple)
        
        #print(alltruth.shape)
        if self.remove:
            print('remove')
            weights=weights[notremoves > 0]
            x_global=x_global[notremoves > 0]
            x_cpf=x_cpf[notremoves > 0]
            x_npf=x_npf[notremoves > 0]
            x_sv=x_sv[notremoves > 0]
            alltruth=alltruth[notremoves > 0]
            pttruth=pttruth[notremoves > 0]
            ptreco=ptreco[notremoves > 0]
       
        newnsamp=x_global.shape[0]
        print('reduced content to ', int(float(newnsamp)/float(self.nsamples)*100),'%')
        self.nsamples = newnsamp
        
        print(x_global.shape,self.nsamples)


        
        self.w=[weights,weights]
        self.x=[x_global,x_cpf,x_npf,x_sv,ptreco]
        self.y=[alltruth,pttruth]
    
