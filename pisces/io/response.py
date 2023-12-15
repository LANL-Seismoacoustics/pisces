import numpy as np
from obspy.core.inventory import response
import warnings

def get_pazfir_lines(path):
    """
    Takes a file path and read in the file into a list where each element is a line
    of the file.  Commented lines are removed so the output only contains the lines 
    described in the file definition.

    Parameters
    ----------
    path: str
        Path to the pazfir file to be read.

    Returns
    -------
    linesActual: list of strings
        List where each list element corresponds to one line of the file represented
        as a string.  Elements are in the same order as lines in the file with
        commented lines not included.

    Examples:
    ---------
    fileLines = get_pazfir_lines('response_file.pazfir')
    """
    
    with open(path, 'r') as f:
        linesAll = f.readlines()

        
        linesActual = []
        
        # Remove commented lines
        for i, line in enumerate(linesAll):
            lineData = line.split()
            if len(lineData) > 0 and lineData[0][0] != '#' :
                linesActual.append(line)
        
    return linesActual


def get_pazfir_metadata(fileLines):
    """
    get_pazfir_metadata takes a list of lines read in from a pazfir type file
    as read in by pazfir_get_lines. The lines from the file that indicate a 
    new stage are identified and the metadata regarding that stage are 
    extracted into a set of lists.

    A line initiating a new response stage in a pazfir file is assumed to take 
    the following form:

        theoretical  1   instrument    paz
    
    where the first variable is assumed to be "theoretical" or "measured", the
    second variable is the sequence number of the response stage, the third is 
    assumed to be "instrument" or "digitizer", and the fourth is the type of 
    response stage, such as paz, fir, fap, or iir.

    For each line initiating a new stage, the above information is extracted 
    and parsed into lists organized by variable type where the index of each 
    list elemnent corresponds to the order that each stage is read in.  The 
    lists are then returned by the function.

    Parameters
    ----------
    fileLines: list of strings
        Output from function get_pazfir_lines where each list element corresponds 
        to one line of the file represented as a string.  Elements are in the same 
        order as lines in the file with commented lines not included.

    Returns
    -------
    stageStart: list of integers
        Index values for lines in fileLines that initiate a new response stage in
        the order they are found in the file.
    stageNums:  list of integers
        Stage numbers extracted from response stage initiation lines in fileLines
        found at the index values in the variable stageStart
    stageType: list of strings
        Stage types as described above extracted from response stage initiation lines 
        in fileLines found at the index values in the variable stageStart
    sourceType:  list of strings
        Stage source in the insturmentation chain, instrument or digitizer, extracted 
        from response stage initiation lines in fileLines found at the index values in 
        the variable stageStart
    t_v_m: list of strings
        Either "theoretical" or "measured" for each stage from response stage initiation 
        lines in fileLines found at the index values in the variable stageStart
    
    Examples:
    ---------
    stageStart, stageNums, stageType, sourceType, t_v_m = get_pazfir_metadata(fileLines)
    """

    #  Get all the stage info to perform checks prior to building stages
    stageStart = []
    t_v_m = []
    stageNums = []
    sourceType = []
    stageType = []

    # iterate through and find the exact lines marking a new stage in the file
    for i, fline in enumerate(fileLines):
        try:
            i_t_v_m, stageNum, i_sourceType, i_stageType, *vars = fline.split()
            if i_t_v_m[0].isalpha():
                t_v_m.append(i_t_v_m)
                stageNums.append(int(stageNum))
                sourceType.append(i_sourceType)
                stageType.append(i_stageType)
                stageStart.append(i)
        except ValueError:
            # data line doesn't contain 4 variables
            pass
    
    return stageStart, stageNums, stageType, sourceType, t_v_m


def get_pazfir_data(fileLines, stageStart, stageType):
    """
    get_pazfir_data takes the metadata lists determeined from get_pazfir_metadata
    and returns lists containing the poles/numerators, zeros/denominators, and 
    sensitivities/decimations of each stage.

    While a pole-zero transfer function has the zeros in the numerator and the 
    poles in the denominator, the structure of the pazfir files have the poles 
    listed before the zeros for paz stages and the numerators listed before the
    denominators for the fir/iir stages.  In order to reduce the number of if 
    statements, each stage proceeds in order which is why the poles are in the 
    same list as the numerators and the zeros are in the same list as the 
    denominators.

    Parameters
    ----------
    fileLines: list of strings
        Output from function get_pazfir_lines where each list element corresponds 
        to one line of the file represented as a string.  Elements are in the same 
        order as lines in the file with commented lines not included.
    stageStart: list of integers, output from get_pazfir_metadata()
        Index values for lines in fileLines that initiate a new response stage in
        the order they are found in the file.
    stageType: list of strings, output from get_pazfir_metadata() 
        Stage types as described above extracted from response stage initiation lines 
        in fileLines found at the index values in the variable stageStart

    Returns
    -------
    poles_nums: list of complex numbers
        Each element in the list is a list of the either the poles for 
        a corresponding paz stage, the numerators of a corresponding fir/iir
        stage, or None for a fap stage
    zeros_denoms: list of complex numbers
        Each element in the list is a list of the either the zeros for 
        a corresponding paz stage, the denominators of a corresponding fir/iir
        stage, or None for a fap stage
    sens_decim: list of floats
        Each element in the list is a list of the either the gain/
        sensitivity for a corresponding paz stage, the sampling frequency 
        of a corresponding fir/iir stage, or None for a fap stage
    
    Examples:
    ---------
    poles_nums, zeros_denoms, sens_decim = get_pazfir_data(fileLines, stageStart, stageType)
    """

    poles_nums = []
    zeros_denoms = []
    sens_decim = []
    
    for i, startVal  in enumerate(stageStart):
        
        if stageType[i] == 'paz' or stageType[i] == 'fir' or stageType[i] == 'iir':
        
            tops = []
            bottoms = []
       
        # get total norm value for paz and decimation sample rate for fir/iir
            startLine = startVal
            stage_constant = float(fileLines[startLine+1])
            sens_decim.append(stage_constant)
           
            # get poles
            num_tops =  int(fileLines[startLine+2])
            lineRange = range(startLine+3, startLine + 3 + num_tops)
                   
            for j in lineRange:
              topData = fileLines[j].split()
              
              if stageType[i] == 'paz':
                  tops.append(complex(float(topData[0]),float(topData[1])))
                  
              elif stageType[i] == 'fir' or stageType[i] == 'iir':
                  tops.append(float(topData[0]))
                  
              else:
                  tops.append(None)
           
            #get zeros
            num_bottoms = int(fileLines[startLine + 3 + num_tops])
            lineRange = range(startLine + 3 + num_tops + 1, startLine + 3 + num_tops + 1 + num_bottoms)
           
            for j in lineRange:
                bottomData = fileLines[j].split()
               
                if stageType[i] == 'paz':
                    bottoms.append(complex(float(bottomData[0]),float(bottomData[1])))
                   
                elif stageType[i] == 'fir' or stageType[i] == 'iir':
                    bottoms.append(float(bottomData[0]))
                   
                else:
                    bottoms.append(None)
            
            poles_nums.append(tops)
            zeros_denoms.append(bottoms)
            
        else:
            tops = None
            bottoms = None
            stage_constant = None
            
            poles_nums.append(tops)
            zeros_denoms.append(bottoms)
            sens_decim.append(stage_constant)
            
    return poles_nums, zeros_denoms, sens_decim


def a0_from_pz(poles, zeros, a0f):
    """
    Calculate a0 from the poles and zeros of a transfer function

    Parameters
    ----------
    poles: list of complex numbers
    zeros: list of complex numbers
    a0f: float
        The frequency at which a0 is to be calculated

    Returns
    -------
    a0: float
        The value of the transfer function at the provided a0f
    
    Examples:
    ---------
    a0 = a0_from_pz(poles, zeros, a0f)
    """
    
    s = 2*np.pi*1j*a0f
    znum = 1.0
    
    for z in zeros:
        ztemp = s - z
        znum *= ztemp
    
    pnum = 1.0
    
    for p in poles:
        ptemp = s - p
        pnum *= ptemp
        
    h = (znum/pnum)
    
    a0 = 1/abs(h)
    
    return a0


def read_pazfir(path, input_samp_rate, calib=None, calper=None, input_units='NM', a0f=1.0, calratio=None):
    """
    Read in a pazfir file and output the instrument response in the form of an obspy 
    response object.

    Parameters
    ----------
    path:  str
    input_sample_rate: float
        The sample rate of the instrument for which the response is valid
    calib: float
        The scaling variable contained in the calib field of an instrument or 
        wfdisc table
    calper: float
        The period at which calib was calculated contained in an instrument 
        or wfdisc table
    input_units: string
        The units of ground motion or pressure being  measured by a 
        seismic or infrasound sensor.  Currently supports displacement in 'M' or 
        'NM' and pressure in pascals, 'PA'.
    a0f: float
        The frequency at which to calculate a0.  If calper is provided, that value
        is converted to frequency and used
    calratio: float
        Calibration conversion ratio found in a KBCore/CSSS3.0 sensor table


    Returns
    -------
    total_resp: obspy.core.inventory.response.Response object
    
    Examples:
    ---------

    """

    warnings.warn('Functionality in development and API subject to change')

    # input units variable only supports "NM", "M", and "PA", default is "NM" as that is the defined
    # units of CSS3.0-like database response information

    # open file and read lines
    linesAll = get_pazfir_lines(path)
    
    # remove commented lines and prep variables to proceed
    stageStart, stageNums, stageType, sourceType, t_v_m = get_pazfir_metadata(linesAll)
    
    # get all numerators, denominators, sensitivities and decimation values
    poles_nums, zeros_denoms, sens_decim = get_pazfir_data(linesAll, stageStart, stageType)
    
    # check consecutive stages and add dummy stages where necessary
    # check if starting stage is 0
    flag = 0
    
    if stageNums[0] == 0:
        stageNums = [n + 1 for n in stageNums]
        flag += 1
        warnings.warn('First stage labeled as stage 0, increasing all stage numbers by one.')
    
    # check if starting stage is greater than 1
    if stageNums[0] > 1:
        diff = stageNums[0]-1
        stageNums = [n + diff for n in stageNums]
        flag += 1
        warnings.warn('First stage number greater than one. Shifting all stage numbers such that the first stage is stage 1.')
    
    # check if stages are consecutive
    stageCheck = 1
    
    if len(stageNums) > 1:
        startNum = 1 
        for i in range(len(stageNums)):
            if stageNums[i] == stageCheck:
                stageCheck +=1
            elif stageNums[i] > stageCheck:
                # dummyInsert.append(stageCheck)
                stageNums.insert(stageCheck-1, stageCheck)
                stageType.insert(stageCheck-1, "dummy")
                stageStart.insert(stageCheck-1, None)
                poles_nums.insert(stageCheck-1, 1.0)
                zeros_denoms.insert(stageCheck-1, 1.0)
                sens_decim.insert(stageCheck-1, 1.0)
                warnings.warn('Stage number missing in file, inserting "dummy" stage at appropriate location')
                stageCheck += 1
            elif stageNums[i] > stageCheck:
                diff = stageCheck - stageNums[i]
                stageNums[i] += diff
                warnings.warn('Stage number lower than expected, increasing by difference between actual and expected')
                stageCheck += 1
                flag +=1
            else:
                warnings.warn('Unusual issues with numbering found, consider evaulating file')
                
    # raise warnings if weird stage numbers
    if flag > 0:
        warnings.warn('Issues found with stage numbering. Proceeding with read, but consider evaulating file')

    # check if consecutive fixes were successful
    stageCheck2 = 1
    for i in range(len(stageNums)):
        if stageNums[i] == stageCheck2:
            stageCheck2 += 1
        else:
            raise ValueError('Stage numbers not consecutive despite attempts to correct')
        
    # Check for no paz and no fap
    pazCount = stageType.count('paz')
    fapCount = stageType.count('fap')
    
    if pazCount == 0 and fapCount == 0:
        warnings.warn('File does not contain PAZ or FAP stage.  Any resultant scaling will not be absolute.')
        
    
    # set units lists and variables
    if input_units == 'M':
        in_desc = 'Displacement in Meters'
    elif input_units == 'PA':
        in_desc = 'Atmospheric Pressure in Pascals'
    else:
        inUput_nits = 'NM'
        in_desc = 'Displacement in Nanometers'
    elec = 'V'
    elec_desc = 'Volts of unknown order of magnitude'
    final = 'COUNTS'
    final_desc = 'Digital Counts'
    
    in_units = []
    out_units = []
    in_units_desc = []
    out_units_desc = []
    
    # check for number of paz stags
    startingPAZ = 0
    
    for i in range(len(stageType)):
        if stageType[i] == 'paz' or stageType[i] == 'dummy':
            startingPAZ +=1
        else:
            break
    
    # set units based on number of paz stages
    if stageType[0] == 'fap':
        in_units.append(input_units)
        out_units.append(final)
        in_units_desc.append(in_desc)
        out_units_desc.append(final_desc)
        subtractNum = 1
        
    elif startingPAZ == 0:
        subtractNum = startingPAZ
    
    elif startingPAZ == 1:
        in_units.append(input_units)
        in_units_desc.append(in_desc)
        out_units.append(final)
        out_units_desc.append(final_desc)
        subtractNum = startingPAZ
            
    elif startingPAZ == 2:
        # first paz stage
        in_units.append(input_units)
        in_units_desc.append(in_desc)
        out_units.append(elec)
        out_units_desc.append(elec_desc)
        # second paz stage
        in_units.append(elec)
        in_units_desc.append(elec_desc)
        out_units.append(final)
        out_units_desc.append(final_desc)
        subtractNum = startingPAZ
        
    elif startingPAZ > 2:
        # first paz stage
        in_units.append(input_units)
        in_units_desc.append(in_desc)
        out_units.append(elec)
        out_units_desc.append(elec_desc)
        # middle paz stages
        if startingPAZ - 2 == 1:
            in_units.append(elec)
            in_units_desc.append(elec_desc)
            out_units.append(elec)
            out_units_desc.append(elec_desc)
        else: 
            for i in range(startingPAZ-2): 
                in_units.append(elec)
                in_units_desc.append(elec_desc)
                out_units.append(elec)
                out_units_desc.append(elec_desc)
        # final paz stage
        in_units.append(elec)
        in_units_desc.append(elec_desc)
        out_units.append(final)
        out_units_desc.append(final_desc)
        subtractNum = startingPAZ
            
    # remaining stages
    for i in range(len(stageType)-subtractNum):
        in_units.append(final)
        out_units.append(final)
        out_units_desc.append(final_desc)
        in_units_desc.append(final_desc)
            
    # calib and calper checks
    calperNull = '-'
    if calper == calperNull or calper is None:
        if calib is None:
            warnings.warn('No calib/calper pair provided. Assumng total scaling is provided in the file.')
            useCals = False
        else:
            warnings.warn('No calper provided with calib. Assumng total scaling is provided in the file.')
            useCals = False
    elif calib is None:
        warnings.warn('No calib provided with calper.  Assumng total scaling is provided in the file.')
        useCals = False
    else:
        useCals = True
        pass
    
    # check FIR stage order and decimation numbers
    
    # print(in_units)
    # print(out_units)
    # print(stageNums)
    # print(stageType)
    # print(stageStart)
    ####     CREATE RESPONSE STAGES
    
    stageList = []
    total_scaling = 1.0
    if useCals == True:
        a0f = 1/calper
    
    ###################    PAZ STAGE   ###########################################
    
    for i, stageVal in enumerate(stageNums):
        if stageType[i] == 'paz':
            
            poles = poles_nums[i]
            zeros = zeros_denoms[i]
            scale = sens_decim[i]
            
            if useCals == True:
                a0 = a0_from_pz(poles, zeros, a0f)
                if calratio is not None:
                    scale = 1/(calib*calratio)
                else:
                    scale = 1/(calib)
            else:
                a0 = a0_from_pz(poles, zeros, a0f)
                scale = scale/a0
                
            if stageVal == 1:
                if input_units == 'M':
                    scale *= 10**9  
                gain = scale
            else:
                gain = 1.0
            
            total_scaling *= gain
            
            # set variables for response stage
            trans_func_type = 'LAPLACE (RADIANS/SECOND)'  # assuming for all db resp files
            
            
            pazStage = response.PolesZerosResponseStage(stageNums[i], gain, a0f, in_units[i],out_units[i],\
                                    trans_func_type, a0f, zeros, poles, \
                                    normalization_factor = a0, \
                                    input_units_description = in_units_desc[i], \
                                    output_units_description = out_units_desc[i])
            
            # start stage list for final input into total Response function
            stageList.append(pazStage)
    
                         
    ########################   FIR /  IIR STAGE  #################################  
          
        elif stageType[i] == 'fir' or stageType[i] == 'iir':
            
            numerators = poles_nums[i]
            denominators = zeros_denoms[i]
                        
            # decimation calculations
            dec_sample_rate = sens_decim[i]
            
            if i < len(stageNums)-1 and stageType[i+1] == 'fir':
                nextSamp = sens_decim[i+1]
                dec_factor = int(dec_sample_rate / nextSamp)
                
            elif i < len(stageNums)-1 and stageNums[i+1] != 'fir':
                nextSamp = input_samp_rate
                dec_factor = int(dec_sample_rate / nextSamp)
                
            elif i == len(stageNums)-1: 
                nextSamp = input_samp_rate
                dec_factor = int( dec_sample_rate / nextSamp)
                
            else:
                warnings.warn('Unexpected issue with FIR stage decimation. Considering evaluating file.')
            
            if useCals == True:
                if calratio is not None:
                    scale = 1/(calib*calratio)
                else:
                    scale = 1/(calib)
            else:
                scale = 1.0
                
            if stageVal == 1:
                gain = scale
            else:
                gain = 1.0
            
            total_scaling *= gain
            
            trans_func_type = 'DIGITAL'   
            
            # Create coefficient response stage for each fir stage
            firStage = response.CoefficientsTypeResponseStage(stageNums[i], gain, \
                                a0f, in_units[i], out_units[i], trans_func_type,\
                                numerator = numerators, denominator = denominators, \
                                decimation_input_sample_rate = dec_sample_rate, \
                                decimation_factor = dec_factor, \
                                decimation_offset = 0, \
                                decimation_delay = 0, \
                                decimation_correction = 0, \
                                input_units_description = in_units_desc[i], \
                                output_units_description = out_units_desc[i])
                
            stageList.append(firStage)
     
    
    #########################    DUMMY STAGE     #################################
               
        elif stageType[i] == 'dummy':
            
            gain = 1.0
            
            # Create coefficient response stage for each fir stage
            firStage = response.CoefficientsTypeResponseStage(stageNums[i], gain, \
                            a0f, in_units[i], out_units[i], 'DIGITAL',\
                            numerator = [], denominator = [], \
                            decimation_input_sample_rate = input_samp_rate, \
                            decimation_factor = 1, \
                            decimation_offset = 0, \
                            decimation_delay = 0, \
                            decimation_correction = 0, \
                            input_units_description = in_units_desc[i], \
                            output_units_description = out_units_desc[i])
            
            stageList.append(firStage)
        
    
    
    #########################    FAP STAGE    ####################################
    
        elif stageType[i] == 'fap':
            
            if useCals == True:
                gain_freq = 1/calper
                if calratio is not None:
                    gain = 1/(calib*calratio)
                else:
                    gain_freq = a0f
                    gain = 1/calib
            else:
                gain_freq = 1.0
                gain = 1.0
                
            if stageVal == 1:
                if input_units == 'M':
                    gain *= 10**9
            else:
                gain = 1.0
            
            total_scaling *= gain
            
            startLine = stageStart[i]
            
            #total number of frequency, amplitude, phase pairs
            num_fap = int(linesAll[startLine+1])
            
            faps = []
            
            for j in range(startLine + 2, startLine + 2 + num_fap):
                fapdat = linesAll[j].split()
                
                frequency = float(fapdat[0])
                amplitude = float(fapdat[1])
                phase = float(fapdat[2])
                
                fapElement = response.ResponseListElement(frequency, amplitude, phase)
                
                faps.append(fapElement)
               
            fapStage = response.ResponseListResponseStage(stageNums[i], gain, a0f, \
                                    in_units[i], out_units[i], response_list_elements = faps, \
                                    input_units_description = in_units_desc[i], \
                                    output_units_description = out_units_desc[i])
            
            stageList.append(fapStage)
    
    ################## GROUP DELAY STAGE
    
    ########################  IS THERE WEIRD SHIT?   #############################
                
        else:
            warnings.warn('Ignoring unexpected stage type {}.  Pazfir files evaulation recommended.'.format(stageType[i]))
            break
        
        
    # create stage 0
    stage0_in_units = stageList[0].input_units
    stage0_in_units_desc = stageList[0].input_units_description
    stage0_out_units = stageList[-1].output_units
    stage0_out_units_desc = stageList[-1].output_units_description
    stage0 = response.InstrumentSensitivity(total_scaling, a0f, stage0_in_units, stage0_out_units, \
                            input_units_description = stage0_in_units_desc,
                            output_units_description = stage0_out_units_desc)
        
    #### CREATE FINAL RESPONSE OBJECT
    
    if "stage0" in locals():
        total_resp = response.Response(response_stages = stageList, instrument_sensitivity = stage0)
    else:
        total_resp = response.Response(response_stages = stageList)
        
        
    return total_resp
