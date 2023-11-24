close all
clear

%read in mumax table files from specified folder, output excel and .mat files with position and velcity extracted

% Specify the folder where the files live.
myFolder = '.\Simulations';

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
filePattern = fullfile(myFolder, '*.out'); % Change to whatever pattern you need.
theFiles = dir(filePattern); %pull the files with this pattern from directory

%for loop to take action on all the files one at a time
for k = 1 : length(theFiles)
    figure(k); %create figure
    
    %get the name of the files & tell user which your reading each loop
    baseFileName = theFiles(k).name;
    fullFileName = fullfile(theFiles(k).folder, baseFileName);
    fprintf(1, 'Now reading %s\n', fullFileName);
    
    % Now do whatever you want with this file name (i.e. read it in)
    
    %file name example for this specific project:
    %DWSim_V=centerWall_Geom=1_Aex=31e-12_Xi=0.01_Ku=5.36e+5_A=0.05_Msat=7.95e+5_u0Hke=NaN_DMI=NaN_J=2.8e+10_RT=20e-9_W=50e-9

    %fileNameParsed is a string array containing
    %each of the parameters for the mumax3 code
    fileNameParsed = split(fullFileName, "_");
    
    %create an excel file and write parameters to it
    fullNameExcel = [fullFileName '.xlsx'];
    writecell(fileNameParsed,fullNameExcel);
    
    %need to read in the table.txt file from this file
    %this is what we will be performing the original matlab code on
    tableFile = [fullFileName '\table.txt'];
    
    %extract the data we will be analyzing
    dataAnalyzed = dlmread(tableFile, '',1,0);
    
    %write data to excel spreadsheet
    %dataTXT = fileread(tableFile);
    %dataXLS = 'table.xlsx';
    %T = readtable(tableFile);
    %writetable(T, dataXLS);
    
    %copied OneNeuron.m here to perform
    %the tests on the data acquired
   
    %looking for number of rows & columns
    %or [rows, columns] = size(dataAnalyzed);
    rows = size(dataAnalyzed,1);
    columns = size(dataAnalyzed,2);
    
    %shift the data in order to find position/velocity values
    dataShift = [ones(rows,1) dataAnalyzed(:,5:columns-3)]; % original data shifted one unit to the right
    dDiff = dataShift-dataAnalyzed(:,5:columns-2); % Think of this as a discrete derivative of d (dd/dx)
    x = 5:columns-2;
    
    %get what J (current density) is for DW is
    jFind = fileNameParsed(13); % depends on file path
    jVal = split(jFind, "=");
    jDW = str2double(jVal(2));
    
    %get runtime for this DW
    rtFind = fileNameParsed(14);
    rtVal = split(rtFind, "=");
    rtVal2 = extractBefore(rtVal, "e");
    rtDWBase = str2double(rtVal2(2));
    rtDW = str2double(rtVal(2));
    
    %reset the current
    Current = zeros(1,rows);
    
    %set the current based on where you are in runtime
    for i=1:rows
        if(dataAnalyzed(i,1) <= rtDW)
            Current(i) = jDW;
        else
            Current(i) = 0;
        end
    end

    %reinitialize the domain wall's position
    dwPosition = zeros(1,rows);

    for i=1:rows
        dwPosition(i)= sum(dDiff(i,:).*x) / sum(dDiff(i,:)); %integral of dd/dx * x * dx divided by integral of dd/dx dx
    end
    dwPositionShift = dwPosition + dataAnalyzed(:,columns-1)'*1e9 - dwPosition(1);

    dwPosition1 = dwPosition( floor((rows+1)/2) );
    dwPosition0 = dwPosition(1);
    calculatedSlope = (dwPosition1 - dwPosition0)/(rtDWBase);

    %mute figures
    set(0, 'DefaultFigureVisible', 'off');
    
    %create the first figure for domain wall position vs time on y axis
    %and current vs time for yy axis
    figure(1);
    plot(dataAnalyzed(:,1)'*1e9,dwPositionShift(:),'b');
    hold on;
    ylabel ('Domain wall position (nm)');
    xlabel ('Time (ns)');
    yyaxis right;
    ylabel ('Current Density (10^1^2 Am^-^2)','Color','r' );
    p = plot(dataAnalyzed(:,1)'*1e9,Current/1e12,'r');
    
    %second page should be the plot from the data gathered above for both current
    %and position
    xlswritefig(p,fullNameExcel,'Sheet2','A1');
    hold off;
    
    %print the plot points on sheet three that coincide with the figures
    fig = findobj(figure(1), 'Type', 'Line' );
    
    x = get(fig, 'Xdata');
    y = get(fig, 'Ydata');
    
    out1 = 'Current Density (10^1^2 Am^-^2) By Time (ns)';
    out2 = 'Domain wall position (nm) By Time (ns)';
    
    try
        xlswrite(fullNameExcel,cellstr(out1),'Sheet3','A1');
        xlswrite(fullNameExcel,x{1},'Sheet3','A2');
        xlswrite(fullNameExcel,y{1},'Sheet3','A3');
    catch
        disp("couldn't write to excel");
    end
    
    try
        xlswrite(fullNameExcel,cellstr(out2),'Sheet3','A5');
        xlswrite(fullNameExcel,x{2},'Sheet3','A6');
        xlswrite(fullNameExcel,y{2},'Sheet3','A7');
    catch
        disp("couldn't write to excel");
    end
    
    %next need to calculate the velocity
    figure(2); %create new figure
    time = dataAnalyzed(:,1);
    n = 2;
    dwPositionShift = dwPositionShift';
    dwNext = circshift(dwPositionShift, [n 0]);
    dwNext(1:n)=0;
    
    timeChange = 2;
    timeNext = circshift(time, [timeChange 0]);
    timeNext(1:timeChange)=0;
    
    delta = (dwPositionShift - dwNext)./(time - timeNext);
    
    %replot the position vs time on y axis & plot velocity vs time on
    %yy axis
    plot(dataAnalyzed(:,1)'*1e9,dwPositionShift(:),'b');
    hold on;
    
    %plot change in position/time to get velocity
    ylabel ('Domain wall position (nm)');
    xlabel ('Time (ns)');
    yyaxis right;
    ylabel ('Domain wall velocity (m/s)','Color','r' ); % change to red
    grid on;
    
    v = plot(time*1e9,delta/1e9,'r');
    
    %add velocity plot to second page
    xlswritefig(v,fullNameExcel,'Sheet2','M1');

    fig2 = findobj(figure(2), 'Type', 'Line' );
    
    x2 = get(fig2, 'Xdata');
    y2 = get(fig2, 'Ydata');
    
    out3 = 'Domain wall velocity (nm) By Time (ns)';
    
    try
        xlswrite(fullNameExcel,cellstr(out3),'Sheet3','A9');
        xlswrite(fullNameExcel,x2{1},'Sheet3','A10');
        xlswrite(fullNameExcel,y2{1},'Sheet3','A11');
    catch
        disp("couldn't write to excel");
    end
    
    % save time, position, and velocity to .mat file
    time = time';
    positionStep = 1e-9;
    dwPosition = dwPositionShift'*positionStep;
    dwVelocity = (delta*positionStep)';
    save(fullfile(theFiles(k).folder, strcat(baseFileName, '.mat')), 'time', 'dwPosition', 'dwVelocity');
    
    %next subtract these
    clf(figure(1));
    clf(figure(2));
    
end
