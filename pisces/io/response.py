import numpy as np
from obspy.core.inventory import response
import warnings
from obspy import read_inventory
from datetime import datetime
from math import pi
from obspy.core import UTCDateTime
import os
from obspy.core.inventory.response import ComplexWithUncertainties, PolesZerosResponseStage, \
    CoefficientsTypeResponseStage,PolynomialResponseStage,ResponseListResponseStage, \
    ResponseStage, FIRResponseStage, FloatWithUncertainties

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
            con_line = fileLines[startLine+1].split()
            stage_constant = float(con_line[0])
            sens_decim.append(stage_constant)
           
            # get poles
            top_line = fileLines[startLine+2].split()
            num_tops =  int(top_line[0])
            lineRange = range(startLine+3, startLine + 3 + num_tops)
                   
            for j in lineRange:
                topData = fileLines[j].split()

                if stageType[i] == 'paz':
                    if len(topData) == 4:
                        if complex(float(topData[2]),float(topData[3])) != 0:
                            topComplex = ComplexWithUncertainties(complex(float(topData[0]),float(topData[1])), upper_uncertainty = complex(float(topData[2]),float(topData[3])), lower_uncertainty = complex(float(topData[2]),float(topData[3])))
                        else:
                            topComplex = ComplexWithUncertainties(complex(float(topData[0]),float(topData[1])))
                    else:
                        topComplex = ComplexWithUncertainties(complex(float(topData[0]),float(topData[1])))
                    tops.append(topComplex)
                    
                elif stageType[i] == 'fir' or stageType[i] == 'iir':
                    if len(topData) == 2:
                        if topData[1] != 0:
                            topVal = FloatWithUncertainties(topData[0], lower_uncertainty = topData[1], upper_uncertainty = topData[1])
                        else:
                            topVal = FloatWithUncertainties(topData[0])
                    else:
                        topVal = FloatWithUncertainties(topData[0])
                    tops.append(topVal)

                else:
                    tops.append(None)
            
            #get zeros
            bot_line = fileLines[startLine + 3 + num_tops].split()
            num_bottoms = int(bot_line[0])
            lineRange = range(startLine + 3 + num_tops + 1, startLine + 3 + num_tops + 1 + num_bottoms)
           
            for j in lineRange:
                bottomData = fileLines[j].split()
               
                if stageType[i] == 'paz':
                    if len(bottomData) == 4:
                        if complex(float(bottomData[2]),float(bottomData[3])) != 0:
                            bottomComplex = ComplexWithUncertainties(complex(float(bottomData[0]),float(bottomData[1])), upper_uncertainty = complex(float(bottomData[2]),float(bottomData[3])), lower_uncertainty = complex(float(bottomData[2]),float(bottomData[3])))
                        else:
                            bottomComplex = ComplexWithUncertainties(complex(float(bottomData[0]),float(bottomData[1])))
                    else:
                        bottomComplex = ComplexWithUncertainties(complex(float(bottomData[0]),float(bottomData[1])))
                    bottoms.append(bottomComplex)
                   
                elif stageType[i] == 'fir' or stageType[i] == 'iir':
                    if len(bottomData) == 2:
                        if bottomData[1] != 0:
                            bottomVal = FloatWithUncertainties(bottomData[0], lower_uncertainty = bottomData[1], upper_uncertainty = bottomData[1])
                        else:
                            bottomVal = FloatWithUncertainties(bottomData[0])
                    else:
                        bottomVal = ComplexWithUncertainties(bottomData[0])
                   
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


def read_pazfir(path, input_samp_rate, calib, calper, input_units, nm_to_m = True, calratio=None):
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
        Specify whether the input file units are in Displacement ('DISP'),
        Velocity ('VEL'), Acceleration ('ACC'), or Pressure ('PRESSURE').  Units of
        displacement, velocity, or acceleration are assumed to be in nanometers
        following the KBCore, CSS3.0, and Antelope specifications.  Units of pressure
        are assumed to be in Pascals.
    nm_to_m: boolean
        Specify whether the output response object is in units displacement, velocity
        or acceleration will be in meters or nanometers.  Default is in meters and
        set to true.
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
    lenStage = len(stageNums)
    
    if lenStage > 1:
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
                warnings.warn('Unusual issues with numbering found, consider evaulating file.')
                
    # raise warnings if weird stage numbers
    if flag > 0:
        warnings.warn('Issues found with stage numbering. Proceeding with read, but consider evaulating file')

    # check if consecutive fixes were successful
    stageCheck2 = 1
    for i in range(len(stageNums)):
        if stageNums[i] == stageCheck2:
            stageCheck2 += 1
        else:
            stageNums = list(range(1,(lenStage+1)))
            # raise ValueError('Stage numbers not consecutive despite attempts to correct')
            warnings.warn('Could not resolve stage numbering.  Numbering consecutively to proceed.')
        
    # Check for no paz and no fap
    pazCount = stageType.count('paz')
    fapCount = stageType.count('fap')
    
    if pazCount == 0 and fapCount == 0:
        warnings.warn('File does not contain PAZ or FAP stage.  Any resultant scaling will not be absolute.')
        
    
    # set units lists and variables
    if input_units == 'DISP':
        units_in = 'NM'
        in_desc = 'Displacement in Nanometers'
    elif input_units == 'PRESSURE':
        units_in = 'PA'
        in_desc = 'Atmospheric Pressure in Pascals'
    elif input_units == 'VEL':
        units_in = 'NM/S'
        in_desc = 'Velocity in in Nanometers/Second'
    elif input_units == 'ACC':
        units_in = 'NM/S**2'
        in_desc = 'Acceleration in Nanometers/Second**2'      
    else:
        raise TypeError('Input unit type not supported.  Accepts DISP, VEL, ACC, or PRESSURE')
        
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
        in_units.append(units_in)
        out_units.append(final)
        in_units_desc.append(in_desc)
        out_units_desc.append(final_desc)
        subtractNum = 1
        
    elif startingPAZ == 0:
        subtractNum = startingPAZ
    
    elif startingPAZ == 1:
        in_units.append(units_in)
        in_units_desc.append(in_desc)
        out_units.append(final)
        out_units_desc.append(final_desc)
        subtractNum = startingPAZ
            
    elif startingPAZ == 2:
        # first paz stage
        in_units.append(units_in)
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
        in_units.append(units_in)
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
            
    # CREATE RESPONSE STAGES
    
    stageList = []
    total_scaling = 1.0
    a0f = 1/calper
    
    # PAZ STAGE
    
    for i, stageVal in enumerate(stageNums):
        if stageType[i] == 'paz':
            
            poles = poles_nums[i]
            zeros = zeros_denoms[i]
            scale = sens_decim[i]

            # Calculate a0 in case a0 in file is incorrect        
            a0 = a0_from_pz(poles, zeros, a0f)
            if calratio is not None:
                scale = 1/(calib*calratio)
            else:
                scale = 1/(calib)

            # adjust scaling and units if converting from nm to m    
            if stageVal == 1:
                if nm_to_m == True:
                    if  input_units == 'DISP':
                        in_units[i] = 'M'
                        in_units_desc[i] = 'Displacement in Meters'
                        scale *= 10**9
                    elif  input_units == 'VEL':
                        in_units[i] = 'M/S'
                        in_units_desc[i] = 'Velocity in Meters/Second'
                        scale *= 10**9
                    elif  input_units == 'ACC':
                        in_units[i] = 'M/S**2'
                        in_units_desc[i] = 'Acceleration in Meters/Second**2'
                        scale *= 10**9
                    else:
                        warnings.warn('Input_unit type cannot be converted from nanometers to meters in any of displacement, velocity, or acceleration')
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
    
                         
    # FIR /  IIR STAGE
          
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
            
            
            if calratio is not None:
                scale = 1/(calib*calratio)
            else:
                scale = 1/(calib)
                
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
     
    
    # DUMMY STAGE if necessary
               
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
        
    
    
    # FAP STAGE 
    
        elif stageType[i] == 'fap':

            if calratio is not None:
                gain = 1/(calib*calratio)
            else:
                gain = 1/calib
                
            if stageVal == 1:
                if nm_to_m == True:
                    if  input_units == 'DISP':
                        in_units[i] = 'M'
                        in_units_desc[i] = 'Displacement in Meters'
                        scale *= 10**9
                    elif  input_units == 'VEL':
                        in_units[i] = 'M/S'
                        in_units_desc[i] = 'Velocity in Meters/Second'
                        scale *= 10**9
                    elif  input_units == 'ACC':
                        in_units[i] = 'M/S**2'
                        in_units_desc[i] = 'Acceleration in Meters/Second**2'
                        scale *= 10**9
                    else:
                        warnings.warn('Input_unit type cannot be converted from nanometers to meters in any of displacement, velocity, or acceleration')
                gain = scale
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
                if phase > 360 or phase < -360:
                    warnings.warn('Phase in fap stage not between -360 and 360.  Wrapping phase to comply with Obspy Angle class limitations which may result in interpolation issues.')

                phase = ((phase+360)%(720)-360) # wrap -360 to 360 to satisfy obspy Angle class limitations
                
                fapElement = response.ResponseListElement(frequency, amplitude, phase)
                
                faps.append(fapElement)
               
            fapStage = response.ResponseListResponseStage(stageNums[i], gain, a0f, \
                                    in_units[i], out_units[i], response_list_elements = faps, \
                                    input_units_description = in_units_desc[i], \
                                    output_units_description = out_units_desc[i])
            
            stageList.append(fapStage)
    
    # GROUP DELAY STAGE

    ### TO DO
    
    # Is there weird shit?
                
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
        
    # CREATE FINAL RESPONSE OBJECT
    
    if "stage0" in locals():
        total_resp = response.Response(response_stages = stageList, instrument_sensitivity = stage0)
    else:
        total_resp = response.Response(response_stages = stageList)
        
        
    return total_resp


def get_errors_from_obspy_uncertainties(varType):

    """
    Takes an ObsPy ComplexWithUncertainties or CoefficientWithUncertainties Object
    and finds the largest uncertainty value or returns 0 if all uncertainties are 
    None.  This is specifically to format pazfir files appropriately.
    
    Parameters
    ----------
    varType: object
        ComplexWithUncertainties or CoefficientWithUncertainties ObsPy object
    Returns
    -------
    vErr: complex or float
        Maximum complex error if input is  ComplexWithUncertainties or float if 
        input is CoefficientWithUncertainties
    """

    varErrors = [varType.lower_uncertainty, varType.upper_uncertainty]
    varErrorNotNone = []

    for vE in varErrors:
        if vE is not None:
            varErrorNotNone.append(vE)

    if len(varErrorNotNone) == 0:
        vErr = 0.0
    else:
        vErr = max(varErrorNotNone)
    
    return vErr

def get_source_type_from_units(inType, outType, stageNum):

    """
    Makes an assumption about the source of the stage, whether it's from a sensor, 
    digitizer, or anti-alias filter based on the input and output units of that 
    stage.  It writes this assumption into file with a a correspondint line in the
    header indicating what assumption was made based on what units.
    
    Parameters
    ----------
    inType: string
        One of finite set of 'DISP','VEL','ACC','PRESSURE', 'TESLA', 'VOLTS', 
        and 'COUNTS' 
    outType: string
        One of finite set of 'VOLTS' and 'COUNTS'
    stageNum: integer
        Number of stage in response sequence
    
    Returns
    -------
    sourceType: string
        One of finite set of 'instrument', 'digitizer', 'antialias', and 'unknown'
    linesOut: string
        Line to be added to the file header
    """

    if inType in ['DISP','VEL','ACC','PRESSURE','TESLA'] and outType in ['VOLTS','COUNTS']:
        sourceType = 'instrument'
        if outType == 'COUNTS':
            linesOut = '# Setting stage {} source description to "instrument" though stage \n# input units are in {} and stage output units are in {}.\n#\n'.format(stageNum, inType, outType)
        else:
            linesOut = '# Assuming stage {} source description is "instrument" as stage \n# input units are in {} and stage output units are in {}.\n#\n'.format(stageNum, inType, outType)
    elif inType == 'VOLTS' and outType == 'VOLTS':
        sourceType = 'digitizer'
        linesOut = '# Assuming stage {} source description is "preamplifier" as stage \n# input units and stage output units are in VOLTS.\n#\n'.format(stageNum)
    elif inType == 'VOLTS' and outType == 'COUNTS':
        sourceType = 'digitizer'
        linesOut = '# Assuming stage {} source description is "digitizer" as stage \n# input units are in VOLTS and stage output units are in COUNTS.\n#\n'.format(stageNum)
    elif inType == 'COUNTS' and outType == 'COUNTS':
        sourceType = 'anti-alias'
        linesOut = '# Assuming stage {} source description is "anti-alias" as stage \n# input units and stage output units are in COUNTS.\n#\n'.format(stageNum)
    else:
        sourceType = 'unknown'
        linesOut = '# Setting stage {} source description to "unknown" as stage \n# input and output units of {} and {} are unexpected combination.\n#\n'.format(stageNum, inType, outType)

    return sourceType, linesOut

def get_stationxml_lines(respStage):

    """
    Extract variables from a response stage to write the contents of that stage to the 
    file header for documentation purposes.

    Parameters
    ----------
    respStage: object
        Input is ObsPy response object of a finite set of types PolesZerosResponseStage,
        CoefficientsTypeResponseStage, FIRResponseStage, and ResponseListResponseStage as 
        well as the ResponseStage parent object.

    Returns
    -------
    respStageLines: string
        Lines to be added to the header describing the input stage object
    """

    respStageLines = '# Stage {}: Original StationXML Stage\n'.format(respStage.stage_sequence_number)
    respStageLines = respStageLines + '#\tInput Units: {} ({})\n'.format(respStage.input_units.upper(),respStage.input_units_description)
    respStageLines = respStageLines + '#\tOutput Units: {} ({})\n'.format(respStage.output_units.upper(),respStage.output_units_description)
    respStageLines = respStageLines + '#\tStage Gain: {} at {} Hz\n'.format(respStage.stage_gain,respStage.stage_gain_frequency)
    respStageLines = respStageLines + '#\tStage Type: {} \n'.format(respStage.__class__.__name__)
    
    if respStage.__class__.__name__ == 'PolesZerosResponseStage':
        respStageLines = respStageLines + '#\tTransfer Function: {} \n'.format(respStage.pz_transfer_function_type)
        respStageLines = respStageLines + '#\tNormalization Factor: {} at {} Hz \n'.format(respStage.normalization_factor, respStage.normalization_frequency)
        respStageLines = respStageLines + '#\tNumber of Poles: {}\n'.format(len(respStage.poles))
        respStageLines = respStageLines + '#\tNumber of Zeros: {}\n'.format(len(respStage.zeros))

    elif respStage.__class__.__name__ == 'CoefficientsTypeResponseStage':
        respStageLines = respStageLines + '#\tTransfer Function: {} \n'.format(respStage.cf_transfer_function_type)
        respStageLines = respStageLines + '#\tNumber of Numerators: {}\n'.format(len(respStage.numerator))
        respStageLines = respStageLines + '#\tNumber of Denominators: {}\n'.format(len(respStage.denominator))
    
    elif respStage.__class__.__name__ == 'FIRResponseStage':
        respStageLines = respStageLines + '#\tTransfer Function: DIGITAL \n'
        respStageLines = respStageLines + '#\tNumber of Numerators: {}\n'.format(len(respStage.coefficients))
    
    elif respStage.__class__.__name__ == 'ResponseListResponseStage':
        respStageLines = respStageLines + '#\tNumber of FAP measurements: {}\n'.format(len(respStage.response_list_elements))
    
    if respStage.decimation_factor is not None:
        respStageLines = respStageLines + '#\tDecimation: \n'
        respStageLines = respStageLines + '#\t\tInput Sample Rate: {}\n'.format(respStage.decimation_input_sample_rate)
        respStageLines = respStageLines + '#\t\tDecimation Factor: {}\n'.format(respStage.decimation_factor)
        respStageLines = respStageLines + '#\t\tDecimation Offset: {}\n'.format(respStage.decimation_offset)
        respStageLines = respStageLines + '#\t\tDecimation Delay: {}\n'.format(respStage.decimation_delay)
        respStageLines = respStageLines + '#\t\tDecimation Correction: {}\n'.format(respStage.decimation_correction)

    respStageLines = respStageLines + '#\n'

    return respStageLines

def write_dict_to_flatfile(tableDict, dirPath = None):

    """
    Take a dictionary with all of the sensor or instrument table colunns as keys with
    lists of values corresponding to each channel or response object in an inventory
    object and output a fixed-width formatted flatfile corresponding to that table.  
    Currently, this function is hard code for only sensor and instrument tables though 
    may be expanded to include more tables in the future.

    Parameters
    ----------
    tableDict: dict
        Sensor or instrument dictionary to be written as a flat file
    dirPath: string
        Directory in which to write the files. If none is provided, the current working
        directory will be used.
    
    Returns
    -------
    Writes file to directory labeled either instrument.txt or sensor.txt
    """

    tableLines = ''
    if tableDict['tablename'] == 'sensor':
        for dex in range(len(tableDict['chanid'])):
            if tableDict['inid'][dex] == -1:
                inidStr = '{:>8s}'.format(str(tableDict['inid'][dex]))
            else:
                inidStr = '{:>8d}'.format(tableDict['inid'][dex])

            if tableDict['chanid'][dex] == -1:
                chanidStr = '{:>8s}'.format(str(tableDict['chanid'][dex]))
            else:
                chanidStr = '{:>8d}'.format(tableDict['chanid'][dex])

            if tableDict['jdate'][dex] == -1:
                jDateStr = '{:>8s}'.format(str(tableDict['jdate'][dex]))
            else:
                jDateStr = '{:>8d}'.format(tableDict['jdate'][dex])

            if tableDict['calratio'][dex] == 1:
                calratioStr = '{:>16s}'.format(str(tableDict['calratio'][dex]))
            else:
                calratioStr = '{:>16.6f}'.format(tableDict['calratio'][dex])

            if tableDict['calper'][dex] == -1:
                calperStr = '{:>16s}'.format(str(tableDict['calper'][dex]))
            else:
                calperStr = '{:>16.6f}'.format(tableDict['calper'][dex])
            
            rowLine = '{:<6s} {:<8s} {:>17.5f} {:>17.5f} {} {} {} {} {} {:>16.2f} {:<1s}\n'.format(\
                tableDict['sta'][dex], tableDict['chan'][dex],tableDict['time'][dex], tableDict['endtime'][dex], inidStr, \
                chanidStr, jDateStr, calratioStr, calperStr, tableDict['tshift'][dex], tableDict['instant'][dex])
            
            tableLines = tableLines + rowLine
        fileName = 'sensor_table.txt'

    elif tableDict['tablename'] == 'instrument':
        for dex in range(len(tableDict['inid'])):
            if tableDict['ncalper'][dex] == 1:
                ncalperStr = '{:>16s}'.format(str(tableDict['ncalper'][dex]))
            else:
                ncalperStr = '{:>16.6f}'.format(tableDict['ncalper'][dex])

            if tableDict['ncalib'][dex] == -1:
                ncalibStr = '{:>16s}'.format(str(tableDict['ncalib'][dex]))
            else:
                ncalibStr = '{:>16.6f}'.format(tableDict['ncalib'][dex])
            rowLine = '{:<8d} {:<50s} {:<6s} {:<1s} {:<1s} {:>11.7f} {} {} {:<64s} {:<32s} {:<6s}\n'.format( \
                tableDict['inid'][dex], tableDict['insname'][dex],tableDict['instype'][dex], tableDict['band'][dex], \
                tableDict['digital'][dex],tableDict['samprate'][dex], ncalibStr, ncalperStr, tableDict['dir'][dex], \
                tableDict['dfile'][dex], tableDict['rsptype'][dex])
            
            tableLines = tableLines + rowLine
        fileName = 'instrument_table.txt'
    
    if dirPath is None:
        dirPath = os.getcwd()

    if dirPath[-1] == '/':
        outpath = '{}{}'.format(dirPath,fileName)
    else:
        outpath = '{}/{}'.format(dirPath,fileName)

    tableFile = open(outpath,'w')
    tableFile.write(tableLines)
    tableFile.close()

    return
    

def write_pazfir(response, station, channel, starttime, out_freq = None, dir_path = None, network = None, location = None, \
                 endtime = None, sample_rate = None,sensor = None, data_logger = None, pre_amplifier = None, **stationDict):
    
    """
    Writes a pazfir style file of file name format like 

    <network>.<station>.<location>.<channel>.<year><julian day>.<extension>

    where the extension is some combination of the stages represented in the file 
    (paz, fir, fap, iir) and returns the sensitivity value at which the file is 
    valid, the frequency at which the sensitivity is calculated, and the filename 
    of the written file.  The ground motion units of the file are in displacement
    in nanometers as this is the file spec defined by CSS3.0 like database schemas.

    Parameters
    ----------
    response: object
        ObsPy Response object to written as a pazfir file
    station: string
        Station code associated with the response (required)
    channel: string
        Channel code associated with the response (required)
    starttime: object
        ObsPy UTCDataTime Object for the starting time at which the response is valid
    out_freq: float
        Frequency at which to calculate the output sensitivity.  If no frequency is 
        provided, the normalization or gain frequency in the first stage of response 
        will be used.
    dir_path: string
        Directory in which to output the pazfir and sensor/instrument files.  If no 
        directory is provided, the current working directory will be selected.
    network: string
        Network Code associated with the response.  Recorded in file header.
    location: string
        Location Code associated with the response. Recorded in file header.
    endtime: object
        ObsPy UTCDataTime Object for the ending time at which the response is valid. 
        Recorded in file header.
    sample_rate: float
        Sampling rate of the channel the response corresponds to.  Recorded in header.
    sensor: string
        Name of the sensor associated with the response. Recorded in header.
    data_logger: string
        Name of the digitizer associated with the response. Recorded in header.
    pre_amplifier: string
       Description of the pre-amplifier associated with the response. Recorded in 
       header.
    stationDict: dict
        For all inputs labeled as "Recorded in header." A dictionary of the values
        with the same input variable names as keys can be used as input instead of 
        assigning each input individually.

    Returns
    -------
    sensitivity: float
        The overall instrument sensitivity associated with the response recorded in 
        the file written to the input directory path or current working directory.
    out_freq: float
        Frequency at which to calculate the output sensitivity.  If out_freq was 
        provided as input, it will be the same, otherwise it will be the 
        normalization or gain frequency in the first stage of response.
    fileName: string
        The name of the file the response was written to.

    Examples:
    ---------
    
    """
    
    # get set of lines to be written in header separate from values lines and combine at the end
    headerLines = "# Response file created using pisces write_pazfir funcion \n# on {}\n#\n".format(datetime.now().strftime('%Y/%m/%d %H:%M'))

    # Add station info to header and assign variables

    headerLines = headerLines + '# Station Information:\n'

    if network is not None:
        pass
    elif 'network' in stationDict:
        network = stationDict['network']
        if network is None or network == '':
            network = 'UNKNOWN'
    else:
        network = 'UNKNOWN'
    headerLines = headerLines + '#\t Network: {}\n'.format(network)

    headerLines = headerLines + '#\t Station: {}\n'.format(station)
    
    if location is not None:
        pass
    elif 'location' in stationDict:
        location = stationDict['location']
        if location is None or location == '':
            location = 'N/A'
    else:
        location = 'N/A'
    headerLines = headerLines + '#\t Location: {}\n'.format(location)
    
    headerLines = headerLines + '#\t Channel: {}\n'.format(channel)
    
    headerLines = headerLines + '#\t Start Date: {}\n'.format(starttime)

    if endtime is not None:
        pass
    elif 'endtime' in stationDict:
        endtime = stationDict['endtime']
        if endtime is None:
            endtime = 'UNKNOWN'
        elif endtime.timestamp == 9999999999.999:
            endtime = 'PRESENT'
    headerLines = headerLines + '#\t End Date: {}\n'.format(endtime)

    if sample_rate is not None:
        pass
    elif 'sample_rate' in stationDict:
        sample_rate = stationDict['sample_rate']
        if sample_rate is None:
            sample_rate = 'UNKNOWN'
    elsesample_rate = 'UNKNOWN'
    headerLines = headerLines + '#\t Sampling Rate: {}\n'.format(sample_rate)
    
    if sensor is not None:
        pass
    elif 'sensor' in stationDict:
        sensor = stationDict['sensor']
        if sensor is None or sensor == '' or sensor == '-':
            sensor = 'UNKNOWN'
    else:
        sensor = 'UNKNOWN'
    headerLines = headerLines + '#\t Sensor: {}\n'.format(sensor)

    if pre_amplifier is not None:
        pass
    if 'pre_amplifier' in stationDict:
        pre_amplifier = stationDict['pre_amplifier']
        if pre_amplifier is not None:
            headerLines = headerLines + '#\t Pre-amplifier: {}\n'.format(pre_amplifier)

    if data_logger is not None:
        pass
    elif 'data_logger' in stationDict:
        data_logger = stationDict['data_logger']
        if data_logger is not None:
            headerLines = headerLines + '#\t Data Logger: {}\n'.format(data_logger)
    
    headerLines = headerLines + '#\n'

    # get frequency from first stage if out_freq is None type 
    if out_freq is None:
        if isinstance(response.response_stages[0],PolesZerosResponseStage):
            out_freq = response.response_stages[0].normalization_frequency
        else:
            out_freq = response.response_stages[0].stage_gain_frequency
        
        headerLines = headerLines + '# No frequency at which to output response information provided.\n'
        headerLines = headerLines + '# Using frequency {} Hz in Stage 1: {}\n#\n'.format(out_freq, response.response_stages[0].__class__.__name__)


    # create a list of lines to be written after header
    linesWrite = ''

    # Bookkeeping for final steps
    extensions = []  # may throw out, what extensions are used to write file?
    delays = []      # XX test this: make sure delays can be summed into one final value and implemented as a final group delay stage

    # Unit handling
    inUnitKey = response.instrument_sensitivity.input_units.upper()
    outUnitKey = response.instrument_sensitivity.output_units.upper()

    unitMap = {"M": "DISP",
                    "NM": "DISP",
                    "CM": "DISP",
                    "MM": "DISP",
                    "M/S": "VEL",
                    "M/SEC": "VEL",
                    "NM/S": "VEL",
                    "NM/SEC": "VEL",
                    "CM/S": "VEL",
                    "CM/SEC": "VEL",
                    "MM/S": "VEL",
                    "MM/SEC": "VEL",
                    "M/S**2": "ACC",
                    "M/(S**2)": "ACC",
                    "M/SEC**2": "ACC",
                    "M/(SEC**2)": "ACC",
                    "M/S/S": "ACC",
                    "NM/S**2": "ACC",
                    "NM/(S**2)": "ACC",
                    "NM/SEC**2": "ACC",
                    "NM/(SEC**2)": "ACC",
                    "CM/S**2": "ACC",
                    "CM/(S**2)": "ACC",
                    "CM/SEC**2": "ACC",
                    "CM/(SEC**2)": "ACC",
                    "MM/S**2": "ACC",
                    "MM/(S**2)": "ACC",
                    "MM/SEC**2": "ACC",
                    "MM/(SEC**2)": "ACC",
                    "V": "VOLTS",
                    "VOLT": "VOLTS",
                    "VOLTS": "VOLTS",
                    "COUNT": "COUNTS",
                    "COUNTS": "COUNTS",
                    "PA": "PRESSURE",
                    "PASCAL": "PRESSURE",
                    "PASCALS": "PRESSURE",
                    "MBAR": "PRESSURE",
                    "T": "TESLA"}
    
    if inUnitKey not in unitMap:
        raise ValueError('Unknown input units of {}'.format(inUnitKey))
    if outUnitKey not in unitMap:
        raise ValueError('Unknown output units of {}'.format(outUnitKey))

    # outUnitType = unitMap[outUnitKey]
    # if outUnitType != 'COUNTS':
    #     raise ValueError('Final response output units must be COUNTS not {}'.format(outUnitType))
    
    inUnitType = unitMap[inUnitKey]
    if inUnitType in ['DISP','VEL','ACC']:
        sensitivity = abs(response.get_evalresp_response_for_frequencies([out_freq], output='DISP')*1.0E-9)[0]
        outUnitType = 'DISP'
        newOutUnits = 'NM'
        if inUnitKey == 'NM':
            headerLines = headerLines + '# Original units are DISP in NM.  No conversion required to \n# match KBCore/CSS3.0 database spec.\n#\n'.format(inUnitType, inUnitKey)
        else:
            headerLines = headerLines + '# Original units are {} in {}.  Converting to DISP in NM to \n# match KBCore/CSS3.0 database spec.\n#\n'.format(inUnitType, inUnitKey)

    elif inUnitType == 'PRESSURE':
        if inUnitKey == 'MBAR':
            sensitivity = abs(response.get_evalresp_response_for_frequencies([out_freq], output='DEF')*100)[0] # convert MBARS to PA
            headerLines = headerLines + '# Original units are PRESSURE in {}.  Converting to PRESSURE in PA to match KBCore database spec.\n#\n'.format(inUnitKey)
        else:
            sensitivity = abs(response.get_evalresp_response_for_frequencies([out_freq], output='DEF'))[0]
            headerLines = headerLines + '# Original units are PRESSURE in PA. No conversion required to match KBCore/CSS3.0 database spec.\n#\n'.format(inUnitKey)
        outUnitType = 'PRESSURE'
        newOutUnits = 'PA'

    else:
        sensitivity = abs(response.get_evalresp_response_for_frequencies([out_freq], output='DEF'))[0]
        headerLines = headerLines + '# Original units are {} in {}.  No unit conversions performed as these units are not included in KBCore/CSS3.0 database spec.\n'.format(inUnitType, inUnitKey)
        outUnitType = unitMap[outUnitKey]
        newOutUnits = outUnitKey
    
    headerLines = headerLines + '# Calculated Sensitivity is {:.6f} at {} Hz in {} in {}\n#\n'.format(sensitivity, out_freq, outUnitType, newOutUnits)
    headerLines = headerLines + '# Stage 0: Original StationXML Instrument Sensitivity Stage \n'
    headerLines = headerLines + '#\tSensitivity value: {} at {} Hz \n'.format(response.instrument_sensitivity.value, response.instrument_sensitivity.frequency)
    headerLines = headerLines + '#\tInput Units: {} ({}) \n'.format(response.instrument_sensitivity.input_units, response.instrument_sensitivity.input_units_description)
    headerLines = headerLines + '#\tOutput Units: {} ({}) \n'.format(response.instrument_sensitivity.output_units, response.instrument_sensitivity.output_units_description)
    headerLines = headerLines + '#\n'

    # firTrigger = False

    # Write each response stage to linesWrite 
    for respStage in response.response_stages:
        stageLines = ''

        if isinstance(respStage,PolesZerosResponseStage):
            if respStage.pz_transfer_function_type == 'DIGITAL (Z-TRANSFORM)':
                    raise NotImplementedError('Conversion of PolesZerosResponseStage transfer function of type "DIGITAL (Z-TRANSFORM)" to type "LAPLACE (RADIANS/SECOND)" not implemented')

            # Make unit based adjustments here
            stageInUnitType = unitMap[respStage.input_units.upper()]
            stageOutUnitType = unitMap[respStage.output_units.upper()]

            if stageInUnitType == 'VEL':
                respStage.zeros.append(ComplexWithUncertainties(0j))
                A0 = a0_from_pz(respStage.poles, respStage.zeros, out_freq)
            elif stageInUnitType == 'ACC':
                respStage.zeros.append(ComplexWithUncertainties(0j))
                respStage.zeros.append(ComplexWithUncertainties(0j))
                A0 = a0_from_pz(respStage.poles, respStage.zeros, out_freq)
            else:
                A0 = a0_from_pz(respStage.poles, respStage.zeros, out_freq)

            # Convert from Laplace(HERTZ) to Laplace (RAD/S)
            funcConv = 1.0

            if respStage.pz_transfer_function_type == 'LAPLACE (HERTZ)':
                funcConv = 2 * pi
                A0 *= funcConv ** (len(respStage.poles) - len(respStage.zeros))
            
            # Set stage info for file
            t_v_m = 'theoretical'  # set paz, fir, iir stages to theoretical, fap stages to measured
            stageType = 'paz'
            stageNum = respStage.stage_sequence_number
            
            sourceType, linesOut = get_source_type_from_units(stageInUnitType, stageOutUnitType, stageNum)
            headerLines = headerLines + linesOut

            dataSource = 'obspy response'

            extensions.append(stageType)

            if respStage.decimation_delay is not None:
                delays.append(respStage.decimation_delay)

            pazLine = '{:<12} {:<2} {:<12} {:<6} {}'.format(t_v_m, stageNum, sourceType, stageType, dataSource)
            stageLines = stageLines + pazLine + '\n'

            stageLines = stageLines + f'{A0: 10.6e}' + '\n'
            
            numPoles = len(respStage.poles)
            numZeros = len(respStage.zeros)
            
            stageLines = stageLines + str(numPoles) +'\n'

            # pazfir only allows for symmetrical error, get largest error between upper and lower and assign to field in pazfir, probably don't need to do the == case

            for p in respStage.poles:

                pReal = p.real * funcConv
                pImag = p.imag * funcConv

                pRealErr = get_errors_from_obspy_uncertainties(p.real) * funcConv
                pImagErr = get_errors_from_obspy_uncertainties(p.imag) * funcConv
                
                stageLines = stageLines + f'{pReal:< 15.6e}' + f'{pImag:< 15.6e}' + f'{pRealErr:< 15.6e}' + f'{pImagErr:< 15.6e}' +'\n'

            stageLines = stageLines + str(numZeros) +'\n'

            for z in respStage.zeros:
                zReal = z.real * funcConv
                zImag = z.imag * funcConv 

                zRealErr = get_errors_from_obspy_uncertainties(z.real) * funcConv
                zImagErr = get_errors_from_obspy_uncertainties(z.imag) * funcConv
                
                stageLines = stageLines + f'{zReal:< 15.6e}' + f'{zImag:< 15.6e}' + f'{zRealErr:< 15.6e}' + f'{zImagErr:< 15.6e}' +'\n'

            linesWrite = linesWrite + stageLines
            respStageLines = get_stationxml_lines(respStage)
            headerLines = headerLines + respStageLines


        elif isinstance(respStage,CoefficientsTypeResponseStage):

            if respStage.cf_transfer_function_type in ['ANALOG (RADIANS/SECOND)','ANALOG (HERTZ)']:
                raise NotImplementedError('Conversion of CoefficientsTypeResponseStage transfer function of type "{}" to type "DIGITAL" not implemented'.format(respStage.cf_transfer_function_type))

            stageInUnitType = unitMap[respStage.input_units.upper()]
            stageOutUnitType = unitMap[respStage.output_units.upper()]
            stageNum = respStage.stage_sequence_number 
            
            sourceType, linesOut = get_source_type_from_units(stageInUnitType, stageOutUnitType, stageNum)
            headerLines = headerLines + linesOut

            numNum = len(respStage.numerator)
            numDenom = len(respStage.denominator)

            if numNum > 0 and numDenom == 0:
                stageExt = 'fir'
                extensions.append(stageExt)
            elif numNum > 0 and numDenom > 0:
                stageExt = 'iir'
                extensions.append(stageExt)
            else:
                headerLines = headerLines + '# No coefficients found.  Skipping stage in file, \n# but gain values are accounted for in sensitivity value.\n#\n'
                respStageLines = get_stationxml_lines(respStage)
                headerLines = headerLines + respStageLines
                continue

            t_v_m = 'theoretical'  # set paz, fir, iir stages to theoretical, fap stages to measured
            stageType = stageExt
            dataSource = 'obspy response'

            decimSampRate = respStage.decimation_input_sample_rate

            if respStage.decimation_delay is not None:
                delays.append(respStage.decimation_delay)

            firLine = '{:<12} {:<2} {:<12} {:<6} {}'.format(t_v_m, stageNum, sourceType, stageType, dataSource)
            stageLines = stageLines + firLine + '\n'
            stageLines = stageLines + f'{decimSampRate: 10.6e}' + '\n'
            stageLines = stageLines + str(numNum) +'\n'

            for n in respStage.numerator:
                nErr = zRealErr = get_errors_from_obspy_uncertainties(n)
                stageLines = stageLines + f'{n:< 15.6e}' f'{nErr:< 15.6e}' + '\n'
            
            stageLines = stageLines + str(numDenom) +'\n'

            if numDenom > 0:
                for d in respStage.denominator:
                    dErr = zRealErr = get_errors_from_obspy_uncertainties(n)
                    stageLines = stageLines + f'{d:< 15.6e}' f'{dErr:< 15.6e}' + '\n'

            linesWrite = linesWrite + stageLines
            respStageLines = get_stationxml_lines(respStage)
            headerLines = headerLines + respStageLines

        elif isinstance(respStage,FIRResponseStage):

            numNum = len(respStage.coefficients)
            
            if numNum > 0:
                stageInUnitType = unitMap[respStage.input_units.upper()]
                stageOutUnitType = unitMap[respStage.output_units.upper()]
                stageNum = respStage.stage_sequence_number
                
                sourceType, linesOut = get_source_type_from_units(stageInUnitType, stageOutUnitType, stageNum)
                headerLines = headerLines + linesOut

                t_v_m = 'theoretical'  # set paz, fir, iir stages to theoretical, fap stages to measured
                stageType = 'fir'
                
                dataSource = 'obspy response' 
                
                extensions.append(stageType)

                if respStage.decimation_delay is not None:
                    delays.append(respStage.decimation_delay)
                
                decimSampRate = respStage.decimation_input_sample_rate

                firLine = '{:<12} {:<2} {:<12} {:<6} {}'.format(t_v_m, stageNum, sourceType, stageType, dataSource)
                stageLines = stageLines + firLine + '\n'
                stageLines = stageLines + f'{decimSampRate: 10.6e}' + '\n'
                stageLines = stageLines + str(numNum) +'\n'

                for n in respStage.coefficients:
                    nErr = zRealErr = get_errors_from_obspy_uncertainties(n)
                    stageLines = stageLines + f'{n:< 15.6e}' f'{nErr:< 15.6e}' + '\n'
                
                stageLines = stageLines + '0' +'\n'

                linesWrite = linesWrite + stageLines
                respStageLines = get_stationxml_lines(respStage)
                headerLines = headerLines + respStageLines

            else:
                headerLines = headerLines + '# No coefficients found.  Skipping stage in file, \n# but gain values are accounted for in sensitivity value.\n#\n'
                respStageLines = get_stationxml_lines(respStage)
                headerLines = headerLines + respStageLines
                continue

        elif isinstance(respStage,ResponseListResponseStage):
            
            stageInUnitType = unitMap[respStage.input_units.upper()]
            stageOutUnitType = unitMap[respStage.output_units.upper()]

            t_v_m = 'theoretical'  # set paz, fir, iir stages to theoretical, fap stages to measured
            stageType = 'fap'
            stageNum = respStage.stage_sequence_number

            sourceType, linesOut = get_source_type_from_units(stageInUnitType, stageOutUnitType, stageNum)
            headerLines = headerLines + linesOut

            dataSource = 'obspy response'

            extensions.append(stageType)

            if respStage.decimation_delay is not None:
                delays.append(respStage.decimation_delay)

            fapLine = '{:<12} {:<2} {:<12} {:<6} {}'.format(t_v_m, stageNum, sourceType, stageType, dataSource)
            stageLines = stageLines + fapLine + '\n'

            fapNum = len(respStage.response_list_elements)
            stageLines = stageLines + str(fapNum) +'\n'

            for e in respStage.response_list_elements:
                freq = e.frequency
                amp = e.amplitude
                pha = e.phase
                
                aErr = get_errors_from_obspy_uncertainties(e.amplitude)
                pErr = get_errors_from_obspy_uncertainties(e.phase)
                
                stageLines = stageLines + f'{freq:<12.8f}' + f'{amp:<12.8f}' + f'{pha:< 13.8f}' + f'{aErr:<12.8f}' + f'{pErr:<12.8f}' + '\n'
            
            linesWrite = linesWrite + stageLines
            respStageLines = get_stationxml_lines(respStage)
            headerLines = headerLines + respStageLines

        elif isinstance(respStage, PolynomialResponseStage):
            raise TypeError('Pazfir file spec does not support Polynomial Responses')

        elif isinstance(respStage, ResponseStage):
            headerLines = headerLines + 'Generic Obspy ResponseStage object in StationXML File. \n# Does not contribute to pazfir type response. \n'
            respStageLines = get_stationxml_lines(respStage)
            headerLines = headerLines + respStageLines
        
        else:
            wrongStage = respStage.__class__.__name__
            raise TypeError('Unsupported Stage Type: {}'.format(wrongStage))
        
    linesWrite = headerLines + '#\n'+ linesWrite
    
    if network == 'UKNOWN': network = '__'
    if location == 'N/A': location = ''
    timeStr = starttime.strftime('%Y%j')
    extSet = set(extensions)
    uniqueExt = list(extSet)
    fileExt = ''
    if 'paz' in uniqueExt:
        fileExt = fileExt + 'paz'
    if 'fir' in uniqueExt:
        fileExt = fileExt + 'fir'
    if 'iir' in uniqueExt:
        fileExt = fileExt + 'iir'
    if 'fap' in uniqueExt:
        fileExt = fileExt + 'fap'

    fileName = '{}.{}.{}.{}.{}.{}'.format(network, station, channel, location, timeStr, fileExt)

    if dir_path is None:
        dir_path = os.getcwd()

    if dir_path[-1] == '/':
        outpath = '{}{}'.format(dir_path,fileName)
    else:
        outpath = '{}/{}'.format(dir_path,fileName)

    respFile = open(outpath,'w')
    # for respLine in linesWrite:
    respFile.write(linesWrite)
    respFile.close()

    return sensitivity, out_freq, fileName
    

def sxml2pazfir(input_xml, out_freq=None, dir_path = None, write_tables = True):
    """
    Takes a StationXML file or an ObsPy Inventory object and writes out a pazfir style file
    for every response contained within the file/object as well as writes optional sensor and 
    instrument flat files with metadata for every channel.  File are automatically named based
    on provided network, station, location, channel, and starttime in year and julian day as 
    well as given a file extenstion descriptive of the stage types contained within the file.
    This is done such that the corresponding file name is not more than 32 characters which is
    the maximum allowed string length for the dir column in the instrument tables for CSS3.0-
    like schemas.  This function will also return the dictionaries used to create the sensor 
    and instrument flatfiles.

    Parameters
    ----------
    input_xml: string or Inventory object
        If a filename  is provided, the file will be read in as an Inventory object
    out_freq: float
        Frequency at which to calculate the output sensitivity.  If no frequency is provided, 
        the normalization or gain frequency in the first stage of response will be used.
    dir_path: string
        Directory in which to output the pazfir and sensor/instrument files.  If no directory
        is provided, the current working directory will be selected.
    write_tables: boolean
        Default is True.  If True, a sensor table, 'sensor.txt', and instrument table, 
       'instrument.txt', formatted according to the KBCore spec will be written to the output
        directory.  If false, no sensor or instrument tables will be written, but the pazfir 
        files will be.

    Returns
    -------
    sensorDict: dict
        Dictionary containing all of the sensor metadata in the Inventory object as  
        specified by the KBCore Schema.  Chanid and Inid are automatically assigned based 
        on channel and response indices in the object
    instrumentDict: dict
        Dictionary containing all of the sensor metadata in Inventory object as 
        specified by the KBCore Schema. Inid is automatically assigned based on the response
        index within the object and will correspond to the correct chanid in the sensor table

    Examples:
    ---------
    sensor, instrument  = sxml2pazfir('stationxml_path', write_tables = False)
    sxml2pazfir(InventoryObject, out_freq = 1.0, dir_path = 'path_to_directory')

    """

    # input can be inv object or file path as string
    if type(input_xml) is str:
        invObj = read_inventory(input_xml)
    else:
        invObj = input_xml

    if dir_path is None:
        dir_path = os.getcwd()
    
    inid = 0
    chanid = 0

    # sta, chan, time, endtime, inid, chanid, jdate, calratio, calper, thsift (clock errors), instant
    sensorDict = {'tablename':'sensor', 'sta':[], 'chan':[], 'time':[], 'endtime':[], 'inid':[], 'chanid':[], \
                  'jdate':[], 'calratio':[], 'calper':[], 'tshift':[], 'instant':[]}
     # inid, insname, instype, band, digital (d/a), samprate, ncalib, ncalper, dir, dfile, rsptype
    instrumentDict = {'tablename':'instrument','inid':[], 'insname':[], 'instype':[], 'band':[], 'digital':[], \
                     'samprate':[], 'ncalib':[], 'ncalper':[], 'dir':[], 'dfile':[], 'rsptype':[]} 

    for net in invObj.networks:
        netCode = net.code
        for sta in net.stations:
            staCode = sta.code
            for chan in sta.channels:
                chanCode = chan.code
                locCode =chan.location_code
                sampRate = chan.sample_rate
                sensorDesc = chan.sensor.description
                startDate = chan.start_date
                endDate = chan.end_date
                dataLogger = chan.data_logger
                preAmp = chan.pre_amplifier
                
                # for table formation
                chanLocCode = chanCode + locCode
                bandCode = chanCode[0].lower()
                jDate = int(startDate.strftime('%Y%j'))

                if sensorDesc is None:
                    sensorDesc = '-'

                if startDate is None:
                    startDate = UTCDateTime(-9999999999.999)
                    jDate 
                if endDate is None:
                    endDate =  UTCDateTime(9999999999.999)
                
                #check if response information exists, if so, go into response loop
                if len(chan.response.response_stages) > 0: 
                    sensitivity, out_freq, fileName =  write_pazfir(chan.response, staCode, chanCode, startDate, out_freq = out_freq, dir_path = dir_path, network=netCode, location=locCode, \
                                                          endtime=endDate, sample_rate=sampRate, sensor=sensorDesc, data_logger=dataLogger, pre_amplifier=preAmp)

                    # inid, insname, instype, band, digital (d/a), samprate, ncalib, ncalper, dir, dfile, resptype
                    ncalper = 1/out_freq
                    ncalib = 1/sensitivity
                    rspType = fileName.split('.')[-1]
                    
                    instrumentDict['inid'].append(inid); instrumentDict['insname'].append(sensorDesc)
                    instrumentDict['instype'].append('-'), instrumentDict['band'].append(bandCode); instrumentDict['digital'].append('d')
                    instrumentDict['samprate'].append(sampRate); instrumentDict['ncalib'].append(ncalib); instrumentDict['ncalper'].append(ncalper)
                    instrumentDict['dir'].append(dir_path), instrumentDict['dfile'].append(fileName); instrumentDict['rsptype'].append(rspType)
                   
                    sensorDict['sta'].append(staCode); sensorDict['chan'].append(chanLocCode)
                    sensorDict['time'].append(startDate.timestamp); sensorDict['endtime'].append(endDate.timestamp); sensorDict['inid'].append(inid)
                    sensorDict['chanid'].append(chanid); sensorDict['jdate'].append(jDate); sensorDict['calratio'].append(1)
                    sensorDict['calper'].append(ncalper); sensorDict['tshift'].append(0); sensorDict['instant'].append('y')
                    
                    inid += 1
                    chanid +=1

                else:
                    sensorDict['sta'].append(staCode); sensorDict['chan'].append(chanLocCode)
                    sensorDict['time'].append(startDate.timestamp); sensorDict['endtime'].append(endDate.timestamp); sensorDict['inid'].append(inid)
                    sensorDict['chanid'].append(chanid); sensorDict['jdate'].append(jDate); sensorDict['calratio'].append(1)
                    sensorDict['calper'].append(-1); sensorDict['tshift'].append(0); sensorDict['instant'].append('y')
                    
                    chanid +=1

    if write_tables == True:
        write_dict_to_flatfile(sensorDict, dir_path)
        write_dict_to_flatfile(instrumentDict, dir_path)

    return sensorDict, instrumentDict