close all;
clear;

% Code for finding model constants from mumax simulation fitting
% Use after running DW_analysis.m for each corner, and compiling all corners' .mat file outputs into single folder
% Create and save lookup tables for model constants

% Specify the folder where the mat files live.
myFolder = 'Simulations\dataAnalysis\lookupTableData';

% Make sure the folder exists
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
fileType = "*.mat"; 
filePattern = fullfile(myFolder, fileType); 
theFiles = dir(filePattern); % pull all .mat files from directory

%create interp tables for constants of model fitting
interp_maxVel_c0 = [];
interp_maxVel_c1 = [];
interp_maxVel_c2 = [];
interp_maxVel_c3 = [];
interp_drift_const = [];
interp_d2 = [];

% list of param corner to keep track of order constants were saved to above tables
param_list = [];


%loop through all param corner .mat files
for k = 1 : length(theFiles)
    
    %load matrix (dataTable) with 4 rows: current, and corresponding maxVel/timeConstant/driftDist
    baseFileName = theFiles(k).name;
    fullFileName = fullfile(theFiles(k).folder, baseFileName);
    load(fullFileName);

    % use ind as upper index, to prevent fitting to data points with J>4e10
    ind = find(dataTable(1,:)>=4e10, 1); 
    if(isempty(ind))
        ind = length(dataTable(1,:));
    end

    % create seperate lists for quantities read in from .mat file
    J = dataTable(1,1:ind);
    maxVel = dataTable(2,1:ind);
    timeConstant = dataTable(3,1:ind)*1e9;
    driftDist = dataTable(4,1:ind)*1e9;
    disp(dataTable);
    
    %get parameter values for current parameter set
    [~, filename_noext, ~] = fileparts(baseFileName);
    
    AexVal = regexp(filename_noext, '_Aex=([^_]+)', 'tokens');
    AexVal = AexVal{1}{1};
    Aex_s = str2double(AexVal) * 1e12; %pJ/m
    
    KuVal = regexp(filename_noext, '_Ku=([^_]+)', 'tokens');
    KuVal = KuVal{1}{1};
    Ku_s = str2double(KuVal); %J/m^3
    
    AVal = regexp(filename_noext, '_A=([^_]+)', 'tokens');
    AVal = AVal{1}{1};
    A_s = str2double(AVal); %Unitless
    
    MsatVal = regexp(filename_noext, '_Msat=([^_]+)', 'tokens');
    MsatVal = MsatVal{1}{1};
    Msat_s = str2double(MsatVal); %A/m
    
    WVal = regexp(filename_noext, '_W=([^_]+)', 'tokens');
    WVal = WVal{1}{1};
    W_s = str2double(WVal) * 1e9; %nm
    
    
    % Using B anis in lookup table instead of Ku
    if(Ku_s == 1.11e6 || Ku_s == 5.36e5)
        B_anis_s = 350;
    elseif(Ku_s == 9.17e5 ||Ku_s == 4.05e5)
        B_anis_s = 20;
    else
        B_anis_s = (Ku_s/(0.5*Msat_s) - (4*pi*1e-7)*Msat_s)*1000;
    end

    % keep order of param coords to match interp_ matrices for later interp
    current_param = [Aex_s,B_anis_s,A_s,Msat_s,W_s];
    param_list = cat(1,param_list,current_param);
    
    
    %only include current range where max velocity increases with current
    if(max(maxVel) ~= maxVel(end))
        maxJind = find(maxVel==max(maxVel),1);
        
        J = J(1:maxJind);
        maxVel = maxVel(1:maxJind);
        disp(maxVel);
        timeConstant = timeConstant(1:maxJind);
        driftDist = driftDist(1:maxJind);

        disp(strcat("Changing current maximum to ",sprintf('%0.2e',J(end))," for ",mat2str(current_param)));
    end
    
    %fit maxVel to eqn a*J^3 + bJ^2 + cJ + d, use Jq/Jq(1) to scale down, adjust coeffs later
    J_fit = J/J(1);
    %fit with weight to make lower values more important & reduce % err at low values
    w = maxVel.^-2;
    cubicModel = @(b,x) b(1).*x.^3 + b(2).*x.^2 + b(3).*x + b(4);
    start = [1; 1; 1; 1];
    cubicFit = fitnlm(J_fit,maxVel,cubicModel,start,'Weight',w);
    cubic_coeffs = cubicFit.Coefficients.Estimate;
    
    % adjust coeffs to work for unscaled J
    c3 = cubic_coeffs(1)/(J(1)^3);
    c2 = cubic_coeffs(2)/(J(1)^2);
    c1 = cubic_coeffs(3)/J(1);
    c0 = cubic_coeffs(4);
    
    %fit drift dist to linear model
    driftDistPlot = [maxVel; driftDist];
    %add weight to earlier (smaller valued) part of fit
    w = driftDistPlot(2,:).^-1;
    linModel = @(b,x) b(1).*x;
    start = 1;
    linFit = fitnlm(driftDistPlot(1,:),driftDistPlot(2,:),linModel,start,'Weight',w);
    drift_fit = linFit.Coefficients.Estimate;
    
    
    %time const has inverse proportional relationship to J
    d2 = J'\(timeConstant.^-1 - 1/drift_fit)';
    if(d2<0)
        d2 = 0;
    end
    
    % update lists with model constants for this corner
    interp_maxVel_c0 = cat(1,interp_maxVel_c0,c0);
    interp_maxVel_c1 = cat(1,interp_maxVel_c1,c1);
    interp_maxVel_c2 = cat(1,interp_maxVel_c2,c2);
    interp_maxVel_c3 = cat(1,interp_maxVel_c3,c3);
    interp_drift_const = cat(1,interp_drift_const,drift_fit);
    interp_d2 = cat(1,interp_d2,d2);
    
end

% write lookup tables to .tbl files
% one lookup table per model constant, lists all param corners with corresponding model constant value

fid = fopen(fullfile(myFolder, 'lookup_maxVel_c0.tbl'),'w+');
fprintf(fid,'#Aex(*1e12), B_anis, A, Msat, W(nm), c0 \n');
formatSpec = '%g %g %g %g %g %g \n';
fprintf(fid,formatSpec,cat(2,param_list,interp_maxVel_c0)');
fclose(fid);

fid = fopen(fullfile(myFolder, 'lookup_maxVel_c1.tbl'),'w+');
fprintf(fid,'#Aex(*1e12), B_anis, A, Msat, W(nm), c1 \n');
formatSpec = '%g %g %g %g %g %g \n';
fprintf(fid,formatSpec,cat(2,param_list,interp_maxVel_c1)');
fclose(fid);

fid = fopen(fullfile(myFolder, 'lookup_maxVel_c2.tbl'),'w+');
fprintf(fid,'#Aex(*1e12), B_anis, A, Msat, W(nm), c2 \n');
formatSpec = '%g %g %g %g %g %g \n';
fprintf(fid,formatSpec,cat(2,param_list,interp_maxVel_c2)');
fclose(fid);

fid = fopen(fullfile(myFolder, 'lookup_maxVel_c3.tbl'),'w+');
fprintf(fid,'#Aex(*1e12), B_anis, A, Msat, W(nm), c3 \n');
formatSpec = '%g %g %g %g %g %g \n';
fprintf(fid,formatSpec,cat(2,param_list,interp_maxVel_c3)');
fclose(fid);

fid = fopen(fullfile(myFolder, 'lookup_drift_const.tbl'),'w+');
fprintf(fid,'#Aex(*1e12), B_anis, A, Msat, W(nm), drift_const \n');
formatSpec = '%g %g %g %g %g %g \n';
fprintf(fid,formatSpec,cat(2,param_list,interp_drift_const)');
fclose(fid);

fid = fopen(fullfile(myFolder, 'lookup_d2.tbl'),'w+');
fprintf(fid,'#Aex(*1e12), B_anis, A, Msat, W(nm), d2 \n');
formatSpec = '%g %g %g %g %g %g \n';
fprintf(fid,formatSpec,cat(2,param_list,interp_d2)');
fclose(fid);

fid = fopen(fullfile(myFolder, 'lookup_all.csv'),'w+');
fprintf(fid,'Aex B_anis A Msat W c0 c1 c2 c3 drift_const d2 \n');
formatSpec = '%g %g %g %g %g %g %g %g %g %g %g \n';
fprintf(fid,formatSpec,cat(2,param_list,interp_maxVel_c0,interp_maxVel_c1,interp_maxVel_c2, interp_maxVel_c3,interp_drift_const,interp_d2)');
fclose(fid);
