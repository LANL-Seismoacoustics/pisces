from traces2db import main

if __name__ == "__main__":
    """If executed from the shell, get options and defaults there, then run
    program."""
    
    main(['-f','/Users/omarcillo/NORSE/*.sac','dbout','-i','testDB4','--wfdisc','wfdiscL','--site','siteL','--lastid','lastidL'])