# -*- coding: utf-8 -*-
########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $URL$
# $Id$
########### SVN repository information ###################
from __future__ import division, print_function
import re
import numpy as np
import numpy.linalg as nl
import GSASIIspc as G2spc
import GSASIIIO as G2IO
import GSASIIpath
GSASIIpath.SetBinaryPath()
submagSite = 'https://www.cryst.ehu.es/cgi-bin/cryst/programs/subgrmag1_general_GSAS.pl?'
bilbaoSite = 'https://www.cryst.ehu.es/cgi-bin/cryst/programs/'
pseudosym = 'pseudosym/nph-pseudosym'

def GetNonStdSubgroups(SGData, kvec,star=False,landau=False,maximal=False):
    '''Run Bilboa's SUBGROUPS for a non-standard space group. 
    This requires doing a post to the Bilboa site, which returns all
    subgroups of the entered space group as the text of a web page 
    with a table containing the space group symbol, the 
    transformation matrix and index for each subgroup.

    :params list kvec: propogation vector as a list of nine string fractions or blank
    :params SGData: space group object (see :ref:`Space Group object<SGData_table>`) 

    :returns: (error,text) error: if True no error or False; where 
      text containts a possible web page text
    '''
    print('''
    For use of SUBGROUPS, please cite:
      Symmetry-Based Computational Tools for Magnetic Crystallography,
      J.M. Perez-Mato, S.V. Gallego, E.S. Tasci, L. Elcoro, G. de la Flor, and M.I. Aroyo
      Annu. Rev. Mater. Res. 2015. 45,217-48.
      doi: 10.1146/annurev-matsci-070214-021008
    ''')
        
        
    def getSpGrp(item):
        return item.replace('<i>','').replace('</i>','').replace('<sub>','').replace('</sub>','')
    
    def getMatVec(item):
        return item.replace('{','[').replace('}',']')
               
    starmag = 'no'
    if star:
        starmag = 'yes'
    land = 'no'
    if landau:
        land = 'yes'
    celtodas = 'no'
    limite = 'spgroup'
    if maximal:
        limite = 'maximal'
    postdict = {'centrosymmetry':'0','crystalsystem':'0','landau':land,
               'eleccion':'subgrmag1_k','inicio':'nostandard','celtodas':celtodas,
               'limite':limite,'list':'Submit','listado':'lista','starmagnetica':starmag,
               'pointgroup':'0','polarity':'0','sub':'1',
               'super':'','tipog':'gesp','wyckoffstrain':''}
    text,table = G2spc.SGPrint(SGData)
    OpList = G2spc.TextOps(text,table,reverse=True)
#    GenList = G2spc.TextGen(SGData,reverse=True)
    for item in OpList:
        item += '\n'
    sym = ""
    for i in OpList:
        if sym: sym += '\n'
        #if sym: sym += ' ' # use this for testing to generate an error in place of previous
        sym += i.lower()
    postdict['generators'] = sym
    for j in [1,2,3]:
        if kvec[3*j-3] == ' ':
            break
        for i,k in zip(('x','y','z'),kvec[3*j-3:3*j]):
            postdict['knm%d%s'%(j,i)] = k
    page = G2IO.postURL(submagSite,postdict)
    if not page:
        print('connection error - not on internet?')
        return None,None
    page = page.replace('<font style= "text-decoration: overline;">','<font>-')
    result = page.replace('&','\n')
    result = result.split('\n')
    SPGPs = []
    MVs = []
    baseList = []
    itemList = []
    superList = []
    altList = []
    start = 0
    for line in result:    #work around bug report from Bilbao
        start += 1
        if 'yesz' in line:
            break
    for line in result[start:]:
        if 'GGG' in line:
            lines = line.split('GGG')
            line = lines[0]
            alts = []
            beg = True
            for sline in lines:
                items = sline.split('z')
                gid = int(items[0])
                if beg:
                    baseList.append(gid)
                    beg = False
                alts.append(gid)
                itemList.append(gid)
                superList.append(getMatVec(items[7]))
                SPGPs.append(getSpGrp(items[4]))
                MVs.append([getMatVec(items[5]),getMatVec(items[6])])
            altList.append(alts)
            for sline in lines[1:]:
                altList.append([])
        else:
            items = line.split('z')
            gid = int(items[0])
            altList.append([gid,])
            baseList.append(gid)
            itemList.append(gid)
            superList.append(getMatVec(items[7]))
            SPGPs.append(getSpGrp(items[4]))
            MVs.append([getMatVec(items[5]),getMatVec(items[6])])
    result = list(zip(SPGPs,MVs,itemList,altList,superList))
    return result,baseList

def GetNonStdSubgroupsmag(SGData, kvec,star=False,landau=False,maximal=False):
    '''Run Bilboa's k-Subgroupsmag for a non-standard space group. 
    This requires doing a post to the Bilboa site, which returns all
    magnetic subgroups of the entered subgroup as the text of a web page 
    with a table containing the BNS magnetic space group symbol, the 
    transformation matrix and index for each subgroup.

    :params list kvec: propogation vector as a list of three numbers
    :params SGData: space group object (see :ref:`Space Group object<SGData_table>`) 

    :returns: (error,text) error: if True no error or False; where 
      text containts a possible web page text
    '''
    print('''
    For use of k-SUBGROUPSMAG, please cite:
      Symmetry-Based Computational Tools for Magnetic Crystallography,
      J.M. Perez-Mato, S.V. Gallego, E.S. Tasci, L. Elcoro, G. de la Flor, and M.I. Aroyo
      Annu. Rev. Mater. Res. 2015. 45,217-48.
      doi: 10.1146/annurev-matsci-070214-021008
    ''')

    def getSpGrp(item):
        return item.replace('<i>','').replace('</i>','').replace('<sub>','').replace('</sub>','')
    
    def getBNS(item):
        spgrp = getSpGrp(item)
        bns = ''
        sid = item.find('<sub>')
        if sid == 8:
            bns = spgrp[1]
            spgrp = '%s_%s %s'%(spgrp[0],bns,spgrp[2:])
        return spgrp,bns
    
    def getMatVec(item):
        return item.replace('{','[').replace('}',']')
               
    starmag = 'no'
    if star:
        starmag = 'yes'
    land = 'no'
    if landau:
        land = 'yes'
    celtodas = 'no'
    limite = 'spgroup'
    if maximal:
        limite = 'maximal'
    postdict = {'centrosymmetry':'0','crystalsystem':'0','landau':land,
               'eleccion':'subgrmag1_k','inicio':'nostandard','celtodas':celtodas,
               'limite':limite,'list':'Submit','listado':'lista','starmagnetica':starmag,
               'pointgroup':'0','polarity':'0','sub':'1.1',
               'super':'','tipog':'gmag','wyckoffstrain':''}
    text,table = G2spc.SGPrint(SGData)
    OpList = G2spc.TextOps(text,table,reverse=True)
#    OpList = G2spc.TextGen(SGData,reverse=True)
    for item in OpList:
        item += '\n'
    sym = ""
    for i in OpList:
        if sym: sym += '\n'
        #if sym: sym += ' ' # use this for testing to generate an error in place of previous
        sym += i.lower()
    postdict['generators'] = sym
    for j in [1,2,3]:
        if kvec[3*j-3] == ' ':
            break
        for i,k in zip(('x','y','z'),kvec[3*j-3:3*j]):
            postdict['km%d%s'%(j,i)] = k
    page = G2IO.postURL(submagSite,postdict)
    if not page:
        print('connection error - not on internet?')
        return None,None
    page = page.replace('<font style= "text-decoration: overline;">','<font>-')
    result = page.replace('&','\n')
    result = result.split('\n')
    start = 0
    for line in result:    #work around bug report from Bilbao
        start += 1
        if 'yesz' in line:
            break
    SPGPs = []
    BNSs = []
    MVs = []
    baseList = []
    itemList = []
    superList = []
    altList = []
    for line in result[start:]:
        if 'GGG' in line:
            lines = line.split('GGG')
            alts = []
            beg = True
            for sline in lines:
                items = sline.split('z')
                gid = int(items[0])
                if beg:
                    baseList.append(gid)
                    beg = False
                alts.append(gid)
                itemList.append(gid)
                superList.append(getMatVec(items[7]))
                spgrp,bns = getBNS(items[4])
                SPGPs.append(spgrp)
                BNSs.append(bns)
                MVs.append([getMatVec(items[5]),getMatVec(items[6])])
            altList.append(alts)
            for sline in lines[1:]:
                altList.append([])
        else:
            items = line.split('z')
            gid = int(items[0])
            altList.append([gid,])
            baseList.append(gid)
            itemList.append(gid)
            superList.append(getMatVec(items[7]))
            spgrp,bns = getBNS(items[4])
            SPGPs.append(spgrp)
            BNSs.append(bns)
            MVs.append([getMatVec(items[5]),getMatVec(items[6])])
    result = list(zip(SPGPs,BNSs,MVs,itemList,altList,superList))
    return result,baseList

def subBilbaoCheckLattice(spgNum,cell,tol=5):
    '''submit a unit cell to  Bilbao PseudoLattice
    '''
    psSite = "http://www.cryst.ehu.es/cgi-bin/cryst/programs/pseudosym/nph-pseudolattice"
    cellstr = '+'.join(['{:.5f}'.format(i) for i in cell])
    datastr = "sgr={:}&cell={:}&tol={:}&submit=Show".format(
        str(int(spgNum)),cellstr,str(int(tol)))
    page = G2IO.postURL(psSite,datastr)
    if not page:
        print('connection error - not on internet?')
        return None
    page = page.replace('<font style= "text-decoration: overline;">','<font>-')
    return page

def parseBilbaoCheckLattice(page):
    '''find the cell options from the web page returned by Bilbao PseudoLattice
    '''
    cellopts = [i for i in page.split('<tr>') if '<td><pre>' in i]
    found = []
    for c in cellopts:
        cells = c.split("pre")[1].split('<')[0].replace('>','').split('\n') # list of cells, 1st is approx
        try:
            acell = [float(i) for i in cells[0].split()]
            xmatA = [c.split('[')[i].split(']')[0].split() for i in (1,2,3)]
            xmat =  np.array([[eval(i) for i in j] for j in xmatA])
            cellmat = nl.inv(xmat).T
        except:
            print('Error processing cell in',c)
            continue
        found.append((acell,cellmat))
    return found
                
def GetStdSGset(SGData=None, oprList=[]):
    '''Determine the standard setting for a space group from either
    a list of symmetry operators or a space group object using the 
    Bilbao Crystallographic Server utility IDENTIFY GROUP 

    :param list oprList: a list of symmetry operations (example: 
       ['x,y,z', '-x,-y,-z']). Supply either this or SGData, not both. 
    :param SGData: from :func:`GSASIIspc.SpcGroup` 
       Supply either this or oprList, not both.

    :returns: (sgnum, sgnam, xformM, offsetV) where:

      * sgnum is the space group number, 
      * sgnam is the space group short H-M name (as used in GSAS-II)
      * xformM is 3x3 numpy matrix relating the old cell & coordinates to the new
      * offsetV is the vector of offset to be applied to the coordinates

      Note that the new cell is given by G2lat.TransformCell([a,b,...],xformM)
    '''
    import re
    Site='https://www.cryst.ehu.es/cgi-bin/cryst/programs/checkgr.pl'

    if not bool(oprList) ^ bool(SGData):
        raise ValueError('GetStdSGset: Muat specify oprList or SGData and not both')
    elif SGData:
        SymOpList,offsetList,symOpList,G2oprList,G2opcodes = G2spc.AllOps(SGData)
        oprList = [x.lower() for x in SymOpList]

    print('''
      Using Bilbao Crystallographic Server utility IDENTIFY GROUP. Please cite:
      Symmetry-Based Computational Tools for Magnetic Crystallography,
      J.M. Perez-Mato, S.V. Gallego, E.S. Tasci, L. Elcoro, G. de la Flor, and M.I. Aroyo
      Annu. Rev. Mater. Res. 2015. 45,217-48.
      doi: 10.1146/annurev-matsci-070214-021008
    ''')
    postdict = {'tipog':'gesp','generators':'\n'.join(oprList)}
    page = G2IO.postURL(Site,postdict)

    # scrape the HTML output for the new space group # and the xform info
    try:
        sgnum = int(re.search('\(No. (\d+)\)',page).group(1))
    except Exception as msg:
        print('error:',msg)
        return [None,None,None,None]
    sgnam = G2spc.spgbyNum[sgnum]
    
    xform = re.split(r'parclose\.png',re.split(r'paropen\.png',page)[1])[0] # pull out section w/Xform matrix
    mat = re.split(r'</pre>',re.split('<pre>',xform)[1])[0].split('\n')
    offsetV = [eval(m.split()[3]) for m in mat]
    xformM = np.array([[float(i) for i in m.split()[:3]] for m in mat])
    return sgnum, sgnam, xformM.T, offsetV

def BilbaoSymSearch1(sgnum, phase, maxdelta=2, angtol=None):
    '''Perform a search for a supergroup consistent with a phase
    using the Bilbao Pseudosymmetry search (PSEUDO) program, see
    C. Capillas, E.S. Tasci, G. de la Flor, D. Orobengoa, J.M. Perez-Mato 
    and M.I. Aroyo. "A new computer tool at the Bilbao Crystallographic 
    Server to detect and characterize pseudosymmetry". Z. Krist. (2011), 
    226(2), 186-196 DOI:10.1524/zkri.2011.1321.
    '''
    
    print('''
      Using the Bilbao Crystallographic Server Pseudosymmetry search (PSEUDO) 
      program; Please cite:
      C. Capillas, E.S. Tasci, G. de la Flor, D. Orobengoa, J.M. Perez-Mato 
      and M.I. Aroyo. "A new computer tool at the Bilbao Crystallographic 
      Server to detect and characterize pseudosymmetry". Z. Krist. (2011), 
      226(2), 186-196 DOI:10.1524/zkri.2011.1321.
    ''')

    postdict = {
        "formulae":'',
        "cifile":'',
        "filename":"",
        "what":'minsup',
        "maxik":'1',
        "onlythisik":'1',
        "mysuper2":'211',
        "x1":'1',
        "x2":'0',
        "x3":'0',
        "y1":'0',
        "y2":'1',
        "y3":'0',
        "z1":'0',
        "z2":'0',
        "z3":'1',
        "x4":'0',
        "y4":'0',
        "z4":'0',
        "submit":'Show',}

    postdict["maxdelta"] = f'{maxdelta:.1f}'
    if angtol: # and monoclinic/triclinic
        postdict["what"] = 'minsup'
        postdict["angtol"] = f'{angtol:.1f}'
    else:
        postdict["angtol"] = '5'
    postdict["stru"] = f'# Space Group ITA number\n{sgnum}\n'
    postdict["stru"] += '# Lattice parameters\n'
    postdict["stru"] += ' '.join([f"{i}" for i in phase['General']['Cell'][1:7]])
    postdict["stru"] += f"\n# number of atoms & atoms\n{len(phase['Atoms'])}\n"
    cx,ct,cs,cia = phase['General']['AtomPtrs']
    for i,atom in enumerate(phase['Atoms'],1):
        el = ''.join([i for i in atom[ct] if i.isalpha()])   # strip to element symbol
        postdict["stru"] += f"{el:4s} {i} - {atom[cx]:.5f} {atom[cx+1]:.5f} {atom[cx+2]:.5f}\n"
        
    savedcookies = {}
    page0 = G2IO.postURL(bilbaoSite+pseudosym,postdict,getcookie=savedcookies)
    open(f'/tmp/pseudosym0.html','w').write(page0)

    # scan output for values to be used next
    valsdict = {} # base for all supergroups 
    csdict = {}   # supergroups w/default selection value
    rowdict = {}  # information in table row for each supergroup
    for row in page0.split('<input'):
        field = row.split('>')[0]
        if 'name=' not in field: continue
        if 'value=' not in field: continue
        name = value = None
        for item in field.split():
            if '=' not in item: continue
            key,val = item.split('=')
            if key.lower() == 'name':
                name = val.replace('"','')
            if key.lower() == 'value':
                value = val.replace('"','')
            if name == 'cs' and value is not None:
                csdict[value] = "checked" in field
                tr = [i.split('>',1)[1].split('</td')[0] for i in row.split('<td')]
                tr[6] = tr[6].replace('<br>','\n')
                tr = [re.sub(r'\<.*?\>','',i).strip() for i in tr]
                rowdict[value] = tr[1:7] + [not 'invalid' in tr[7]]
                break
            elif name is not None and value is not None:
                if name in valsdict and type(valsdict[name]) is str:
                    valsdict[name] = [valsdict[name],value]
                elif name in valsdict:
                    valsdict[name] += [value]
                else:
                    valsdict[name] = value
                break
    return valsdict,csdict,rowdict,savedcookies
            
def BilbaoSymSearch2(valsdict,csdict,savedcookies):
    structures = {}
    for num in csdict:
        if csdict[num]:
            #print(f"processing {num}")
            postdict = {}
            postdict.update(valsdict)
            postdict['cs'] = num
            page1 = G2IO.postURL(bilbaoSite+pseudosym,postdict,usecookie=savedcookies)
            superdat = page1.split('Idealized structure (supergroup setting')
            if len(superdat) >= 2:
                structures[num] = superdat[1].split('<pre>')[1].split('</pre'
                                    )[0].replace('\t',' ').split('\n')
    return structures


def test():
    '''This tests that routines in Bilbao Crystallographic Server 
    are accessible and produce output that we can parse. The output 
    is displayed but not checked to see that it agrees with what 
    has been provided previously.
    '''    
    SGData = G2spc.SpcGroup('f d -3 m')[1]
    
    print('test SUBGROUPSMAG')
    results,baseList = GetNonStdSubgroupsmag(SGData,('0','0','0',' ',' ',' ',' ',' ',' ',' '))
    print(results)
    if results:
        for [spgp,bns,mv,gid,altList,supList] in results:
            if gid in baseList:
                print('Space group: %d %s BNS: %s'%(gid,spgp,bns))
                print('MV',mv)
                print('altList:',altList)
                print('superList: ',supList)
                
    print('\n\ntest SUBGROUPS')
    results,baseList = GetNonStdSubgroups(SGData,('1/3','1/3','1/2',' ',' ',' ',' ',' ',' ',' '))
    print(results)
    if results:
        for [spgp,mv,gid,altList,supList] in results:
            if gid in baseList:
                print('Space group: %d %s'%(gid,spgp))
                print('MV',mv)
                print('altList:',altList)
                print('superList: ',supList)
                
    print('\n\ntest Bilbao IDENTIFY GROUP')
    sgnum,sgsym,xmat,xoff = GetStdSGset(G2spc.SpcGroup('R 3 C r')[1])
    if sgnum:
        print(f'Space group R3c (rhomb) transforms to std setting: {sgsym} (#{sgnum})')
        print('  xform matrix',xmat)
        print('  coord offset:',xoff)

if __name__ == '__main__':
    # run self-tests
    selftestquiet = False
    test()
    print ("OK")
