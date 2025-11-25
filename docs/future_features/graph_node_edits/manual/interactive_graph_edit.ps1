# Interactive Graph Editor - PowerShell CLI
# 
# Use this for ONE-OFF edits or CONTROVERSIAL items that need manual review.
# For bulk/pattern-based fixes, use bulk_graph_fixes.py instead.
#
# Usage:
#   .\interactive_graph_edit.ps1

param(
    [string]$WorkingDir = ".\rag_storage"
)

# Set strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Colors for output
$ColorSuccess = "Green"
$ColorError = "Red"
$ColorWarning = "Yellow"
$ColorInfo = "Cyan"
$ColorPrompt = "Magenta"

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host ("=" * 80) -ForegroundColor $ColorInfo
    Write-Host $Title -ForegroundColor $ColorInfo
    Write-Host ("=" * 80) -ForegroundColor $ColorInfo
    Write-Host ""
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor $ColorSuccess
}

function Write-ErrorMsg {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor $ColorError
}

function Write-WarningMsg {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor $ColorWarning
}

function Write-InfoMsg {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor $ColorInfo
}

function Get-UserChoice {
    param(
        [string]$Prompt,
        [string[]]$Options
    )
    
    Write-Host ""
    Write-Host $Prompt -ForegroundColor $ColorPrompt
    for ($i = 0; $i -lt $Options.Length; $i++) {
        Write-Host "  [$($i + 1)] $($Options[$i])"
    }
    Write-Host ""
    
    do {
        $choice = Read-Host "Enter choice (1-$($Options.Length))"
        $choiceNum = [int]$choice
    } while ($choiceNum -lt 1 -or $choiceNum -gt $Options.Length)
    
    return $Options[$choiceNum - 1]
}

function Get-UserConfirmation {
    param([string]$Message)
    
    Write-Host ""
    Write-Host $Message -ForegroundColor $ColorPrompt
    $response = Read-Host "Continue? (y/n)"
    return $response -eq 'y' -or $response -eq 'Y' -or $response -eq 'yes'
}

function Load-GraphStructure {
    $graphmlPath = Join-Path $WorkingDir "graph_chunk_entity_relation.graphml"
    
    if (-not (Test-Path $graphmlPath)) {
        Write-ErrorMsg "GraphML file not found: $graphmlPath"
        exit 1
    }
    
    Write-InfoMsg "Loading graph structure..."
    
    [xml]$graphml = Get-Content $graphmlPath
    $ns = @{g = "http://graphml.graphdrawing.org/xmlns"}
    
    $nodes = $graphml | Select-Xml -XPath "//g:node" -Namespace $ns | ForEach-Object {
        $node = $_.Node
        $nodeData = @{
            id = $node.id
        }
        
        foreach ($data in $node.data) {
            $key = $data.key
            $value = $data.'#text'
            
            switch ($key) {
                "d0" { $nodeData.entity_name = $value }
                "d1" { $nodeData.entity_type = $value }
                "d2" { $nodeData.description = $value }
            }
        }
        
        $nodeData
    }
    
    $edges = $graphml | Select-Xml -XPath "//g:edge" -Namespace $ns | ForEach-Object {
        $edge = $_.Node
        @{
            id = $edge.id
            source = $edge.source
            target = $edge.target
        }
    }
    
    Write-Success "Loaded $($nodes.Count) nodes and $($edges.Count) edges"
    
    return @{
        nodes = $nodes
        edges = $edges
    }
}

function Find-IsolatedNodes {
    param(
        [array]$Nodes,
        [array]$Edges,
        [int]$Threshold = 3
    )
    
    # Count edges per node
    $edgeCount = @{}
    foreach ($edge in $Edges) {
        $src = $edge.source
        $tgt = $edge.target
        
        if (-not $edgeCount.ContainsKey($src)) {
            $edgeCount[$src] = 0
        }
        if (-not $edgeCount.ContainsKey($tgt)) {
            $edgeCount[$tgt] = 0
        }
        
        $edgeCount[$src]++
        $edgeCount[$tgt]++
    }
    
    # Find isolated nodes
    $isolated = @()
    foreach ($node in $Nodes) {
        $nodeId = $node.id
        $count = if ($edgeCount.ContainsKey($nodeId)) { $edgeCount[$nodeId] } else { 0 }
        
        if ($count -lt $Threshold) {
            $node.edge_count = $count
            $isolated += $node
        }
    }
    
    return $isolated
}

function Show-NodeDetails {
    param([hashtable]$Node)
    
    Write-Host ""
    Write-Host "Node: $($Node.entity_name)" -ForegroundColor $ColorInfo
    Write-Host "  ID: $($Node.id)"
    Write-Host "  Type: $($Node.entity_type)"
    Write-Host "  Edges: $($Node.edge_count)"
    Write-Host "  Description: $($Node.description.Substring(0, [Math]::Min(150, $Node.description.Length)))..."
    Write-Host ""
}

function Add-Relationship {
    param(
        [string]$SourceEntity,
        [string]$TargetEntity,
        [string]$RelationshipType,
        [string]$Description,
        [double]$Weight = 0.9
    )
    
    Write-InfoMsg "Creating relationship..."
    Write-Host "  Source: $SourceEntity"
    Write-Host "  Target: $TargetEntity"
    Write-Host "  Type: $RelationshipType"
    Write-Host "  Description: $Description"
    Write-Host "  Weight: $Weight"
    
    # Create Python script to add relationship
    $pythonScript = @"
import asyncio
from lightrag import LightRAG

async def add_relationship():
    rag = LightRAG(working_dir='$WorkingDir')
    
    await rag.acreate_relation(
        source_entity='$SourceEntity',
        target_entity='$TargetEntity',
        relation_data={
            'description': '$Description',
            'relationship_type': '$RelationshipType',
            'weight': $Weight
        }
    )
    
    print('✅ Relationship created successfully')

asyncio.run(add_relationship())
"@
    
    $tempScript = [System.IO.Path]::GetTempFileName() + ".py"
    $pythonScript | Out-File -FilePath $tempScript -Encoding utf8
    
    try {
        python $tempScript
        Write-Success "Relationship added successfully!"
    }
    catch {
        Write-ErrorMsg "Failed to add relationship: $_"
    }
    finally {
        Remove-Item $tempScript -ErrorAction SilentlyContinue
    }
}

function Interactive-FixIsolatedNode {
    param([hashtable]$Node)
    
    Show-NodeDetails -Node $Node
    
    $action = Get-UserChoice -Prompt "What would you like to do?" -Options @(
        "Add relationship to program (MCPP II Program)",
        "Add relationship to SOW",
        "Add custom relationship",
        "Skip this node"
    )
    
    switch ($action) {
        "Add relationship to program (MCPP II Program)" {
            $target = "MCPP II Program"
            $relType = "CHILD_OF"
            $desc = "$($Node.entity_name) is part of MCPP II Program"
            
            if (Get-UserConfirmation "Add CHILD_OF relationship to '$target'?") {
                Add-Relationship -SourceEntity $Node.entity_name -TargetEntity $target `
                    -RelationshipType $relType -Description $desc
            }
        }
        "Add relationship to SOW" {
            $target = "MCPP II SOW"
            $relType = "COMPONENT_OF"
            $desc = "$($Node.entity_name) specified in Statement of Work"
            
            if (Get-UserConfirmation "Add COMPONENT_OF relationship to '$target'?") {
                Add-Relationship -SourceEntity $Node.entity_name -TargetEntity $target `
                    -RelationshipType $relType -Description $desc
            }
        }
        "Add custom relationship" {
            Write-Host ""
            $target = Read-Host "Enter target entity name"
            $relType = Get-UserChoice -Prompt "Select relationship type" -Options @(
                "CHILD_OF",
                "COMPONENT_OF",
                "REFERENCES",
                "RELATED_TO",
                "CONTAINS"
            )
            $desc = Read-Host "Enter description"
            
            if (Get-UserConfirmation "Add $relType relationship to '$target'?") {
                Add-Relationship -SourceEntity $Node.entity_name -TargetEntity $target `
                    -RelationshipType $relType -Description $desc
            }
        }
        "Skip this node" {
            Write-InfoMsg "Skipping node..."
        }
    }
}

function Main {
    Write-Header "Interactive Graph Editor - PowerShell CLI"
    
    Write-Host "Working Directory: $WorkingDir" -ForegroundColor $ColorInfo
    Write-Host ""
    Write-Host "This tool is for ONE-OFF edits and CONTROVERSIAL items." -ForegroundColor $ColorWarning
    Write-Host "For bulk/pattern-based fixes, use: python bulk_graph_fixes.py" -ForegroundColor $ColorWarning
    Write-Host ""
    
    # Load graph
    $graph = Load-GraphStructure
    
    # Main menu
    $action = Get-UserChoice -Prompt "What would you like to do?" -Options @(
        "Fix isolated nodes (interactive review)",
        "Add single relationship (manual)",
        "Exit"
    )
    
    switch ($action) {
        "Fix isolated nodes (interactive review)" {
            Write-Header "Finding Isolated Nodes"
            
            $isolated = Find-IsolatedNodes -Nodes $graph.nodes -Edges $graph.edges -Threshold 3
            
            if ($isolated.Count -eq 0) {
                Write-Success "No isolated nodes found!"
                return
            }
            
            Write-InfoMsg "Found $($isolated.Count) isolated nodes (edge count < 3)"
            Write-Host ""
            
            if (-not (Get-UserConfirmation "Review nodes interactively?")) {
                Write-InfoMsg "Cancelled"
                return
            }
            
            foreach ($node in $isolated) {
                Write-Header "Reviewing Node $($isolated.IndexOf($node) + 1) of $($isolated.Count)"
                Interactive-FixIsolatedNode -Node $node
                Write-Host ""
            }
            
            Write-Success "Interactive review complete!"
        }
        "Add single relationship (manual)" {
            Write-Header "Add Manual Relationship"
            
            Write-Host ""
            $source = Read-Host "Enter source entity name"
            $target = Read-Host "Enter target entity name"
            
            $relType = Get-UserChoice -Prompt "Select relationship type" -Options @(
                "CHILD_OF",
                "COMPONENT_OF",
                "REFERENCES",
                "RELATED_TO",
                "CONTAINS",
                "GUIDES",
                "EVALUATED_BY"
            )
            
            $desc = Read-Host "Enter description"
            $weightStr = Read-Host "Enter weight (0.0-1.0, default 0.9)"
            $weight = if ([string]::IsNullOrWhiteSpace($weightStr)) { 0.9 } else { [double]$weightStr }
            
            if (Get-UserConfirmation "Add $relType relationship: '$source' → '$target'?") {
                Add-Relationship -SourceEntity $source -TargetEntity $target `
                    -RelationshipType $relType -Description $desc -Weight $weight
            }
            else {
                Write-InfoMsg "Cancelled"
            }
        }
        "Exit" {
            Write-InfoMsg "Exiting..."
            return
        }
    }
}

# Run main
try {
    Main
}
catch {
    Write-ErrorMsg "An error occurred: $_"
    Write-Host $_.ScriptStackTrace -ForegroundColor $ColorError
    exit 1
}
