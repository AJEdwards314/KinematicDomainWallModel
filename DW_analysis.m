close all;
clear;

% Calculates various quantities (drift distance, time constant of velocity, max velocity) for each current density
% Should be run after extract_DW_motion, using the output .mat files

% Specify the folder where the mat files live - folder contains all mat
% files for particular corner over multiple current densities
% example folder format: ".\Simulations\dataAnalysis\W=50e-9\Aex=11e-12\Xi=0.01_Ku=1.11e+6_A=0.05_Msat=1.2e+6"
folderPattern = '.\Simulations\dataAnalysis\W=50e-9\Aex=11e-12\Xi=*'; 

% if there are multiple folders matching pattern, each corresponding to a
% different parameter corner, loop through folders
folders = dir(folderPattern);
for n = 1: length(folders)
    myFolder = fullfile(folders(n).folder, folders(n).name);
    disp(myFolder);
    
    % Check to make sure that folder actually exists.  Warn user if it doesn't.
    if ~isfolder(myFolder)
        errorMessage = sprintf('Error: The following folder does not exist:\n%s\nPlease specify a new folder.', myFolder);
        uiwait(warndlg(errorMessage));
        myFolder = uigetdir(); % Ask for a new one.
        if myFolder == 0
             % User clicked Cancel
             return;
        end
    end

    % Get a list of all files in the folder with the desired file name pattern.
    fileType = '*out.mat'; %xlsx or mat
    filePattern = fullfile(myFolder, fileType); % Change to whatever pattern you need.
    theFiles = dir(filePattern); %pull the files with this pattern from directory

    jVals = zeros(1,length(theFiles));
    maxVel = zeros(1,length(theFiles));
    timeConstant = zeros(1,length(theFiles));
    driftDist = zeros(1,length(theFiles));
    velJump = zeros(1,length(theFiles));

    % loop through each simulation .mat file
    for k = 1 : length(theFiles)

        %get the name of the files & tell user which your reading each loop
        baseFileName = theFiles(k).name;
        fullFileName = fullfile(theFiles(k).folder, baseFileName);
        fprintf(1, 'Now reading %s\n', fullFileName);

        %fileNameParsed is a string array containing
        %each of the parameters for the mumax3 code
        fileNameParsed = split(baseFileName, "_");

        %read in data from either excel or mat file
        if(strcmp(fileType, '*.xlsx'))
            %get time, position, and velocity from excel sheet
            time = readmatrix(fullFileName,'Sheet',3,'Range','2:2');
            dwPosition = readmatrix(fullFileName,'Sheet',3,'Range','7:7');
            dwVelocity = readmatrix(fullFileName,'Sheet',3,'Range','11:11');
        elseif(strcmp(fileType, '*out.mat'))
            load(fullFileName);
        end

        [~, filename_noext, ~] = fileparts(baseFileName);
    
        %get what J (current density) is for DW is
        jVal = regexp(filename_noext, '_J=([^_]+)', 'tokens');
        jVal = jVal{1}{1};
        jDW = str2double(jVal)
    
        %get runtime for this DW
        rtVal = regexp(filename_noext, '_RT=([^_]+)', 'tokens');
        rtVal = rtVal{1}{1};
        rtDW = str2double(rtVal)

        %reset the current
        Current = zeros(1,length(time));

        %set the current based on where you are in runtime
        current_end = -1;
        for i=1:length(time)
            if(time(i) <= rtDW)
                Current(i) = jDW;
            else
                if(current_end == -1)
                    current_end = i;
                end
                Current(i) = 0;
            end
        end

        % smooth velocity
        smoothVel = smoothdata(dwVelocity,'gaussian',150);

        %plot position/velocity figure
        %{
        figure(1); %create new figure

        %plot the position vs time on y axis & plot velocity vs time on
        %yy axis
        plot(time*1e9,dwPosition*1e9,'b','DisplayName','DW position');
        hold on;
        ylabel ('Domain wall position (nm)');
        xlabel ('Time (ns)');

        yyaxis right;
        ylabel ('Domain wall velocity (m/s)','Color','r' );
        set(gca,'ycolor','r');
        plot(time*1e9,smoothVel,'-','Color','r','DisplayName','DW velocity');
        legend()


        %save plot as png
        try
            saveas(figure(1), strcat(fullFileName, 'smooth.png'));
        catch
            disp('Couldn''t save figure');
        end
        %}

        %plot with current density
        %{
        figure(2);
        plot(time*1e9,dwPosition*1e9,'b','DisplayName','DW position');
        hold on;
        ylabel ('Domain wall position (nm)');
        xlabel ('Time (ns)');
        yyaxis right;
        ylabel ('Current Density (10^1^0 Am^-^2)','Color','r' );
        p = plot(time*1e9,Current/1e10,'r','DisplayName','Current Density');
        ylim([-Current(1)/1e10*0.1 Current(1)/1e10*1.1 ]);
        set(gca,'ycolor','r');
        legend()
        %saveas(figure(2), strcat(fullFileName,'_current', '.png'));
        %}
        
        disp(['Final position: ' num2str(dwPosition(end))]);

        %save current, maxVel, velocity time constant, driftDist, velJump, compile
        %in dataTable to fit model constants to simulation
        jVals(k) = jDW;
        maxVel(k) = max(abs(smoothVel(find(time>rtDW-1,1):current_end-1)));                         % max velocity reached (velocity right before current off)
        timeConstant(k) = time(find(abs(smoothVel-smoothVel(current_end-1))<maxVel(k)/exp(1), 1));  % time when velocity reaches (1-1/e)*maxVel
        driftDist(k) = abs(dwPosition(end)-dwPosition(current_end));                                % distance traveled after current off
        
        % warn if DW still moving at end of simulation, need longer runtime
        if(abs(smoothVel(end))>0.01*maxVel(k))
            disp("DW not stopped")
        end

        % clear figures
        % clf(figure(1));
        % clf(figure(2));
    end


    %for naming
    underscores = strfind(baseFileName, '_');
    width = extractBetween(baseFileName, underscores(12), '.');     % depends on path to files
    substr = char(strcat(baseFileName(underscores(3)+1:underscores(8)-1),width));

    % compile quantities into single table, sort table by current density
    dataTable = [jVals; maxVel; timeConstant; driftDist];
    dataTable = sortrows(dataTable')';

    % save table to same folder
    save(fullfile(theFiles(1).folder, strcat('dataTable_',substr,'.mat')), "dataTable");
end

