#!/usr/bin/env perl
# data_processor.pl
use strict;
use warnings;
use v5.26;

use JSON::PP;
use DBI;
use DateTime;

# Import CPAN modules
use HTTP::Tiny;
use Getopt::Long;
use File::Spec::Functions qw(catfile);

# Configuration
my $config_file = catfile($ENV{HOME}, '.config', 'data_processor.json');
my $config = do {
    open my $fh, '<', $config_file or die "Cannot open config file: $!";
    local $/;
    my $json = <$fh>;
    decode_json($json);
};

# Database connection
my $dbh = DBI->connect(
    "dbi:mysql:database=$config->{db_name};host=$config->{db_host}",
    $config->{db_user},
    $config->{db_pass},
    { RaiseError => 1, AutoCommit => 0 }
);

# Simple function to process data
sub process_data {
    my ($input_file) = @_;
    my @results;
    
    open my $fh, '<', $input_file or die "Cannot open $input_file: $!";
    while (my $line = <$fh>) {
        chomp $line;
        push @results, $line if $line =~ /^data:/;
    }
    
    return \@results;
}