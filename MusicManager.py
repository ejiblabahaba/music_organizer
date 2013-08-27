#music directory tool interface
from FormatTools import *
from NamingTools import *

if __name__ == '__main__':
        """Use this to form commands to inject into MusicManager interface."""
        print "This is the main function."
        
        suggGen = createSuggestions(getUnformattedFolders())
        writeWrapper(project_dir + '\\proposed.txt',[x for x in suggGen])

        # writeWrapper('clean suggestions.txt')
