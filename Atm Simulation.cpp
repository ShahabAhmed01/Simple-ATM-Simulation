/*
    atm.cpp  --  Visually Stunning ATM Simulation
    ----------------------------------------------
    Compile:  g++ -std=c++17 -o atm atm.cpp
    Run:      ./atm
    Windows:  Use Windows Terminal for full color support
*/

#include <iostream>
#include <iomanip>
#include <string>
#include <vector>
#include <sstream>
#include <limits>
#include <ctime>
#include <algorithm>
#include <thread>
#include <chrono>

#ifdef _WIN32
  #ifndef ENABLE_VIRTUAL_TERMINAL_PROCESSING
    #define ENABLE_VIRTUAL_TERMINAL_PROCESSING 0x0004
  #endif
  #include <windows.h>
#endif

using namespace std;

// ================================================================
//  ANSI COLOR PALETTE
// ================================================================
namespace C {
    const string RST  = "\033[0m";
    const string BOLD = "\033[1m";
    const string DIM  = "\033[2m";

    const string RED  = "\033[31m";
    const string GRN  = "\033[32m";
    const string YLW  = "\033[33m";
    const string BLU  = "\033[34m";
    const string MAG  = "\033[35m";
    const string CYN  = "\033[36m";
    const string WHT  = "\033[37m";

    const string BRED = "\033[91m";
    const string BGRN = "\033[92m";
    const string BYLW = "\033[93m";
    const string BBLU = "\033[94m";
    const string BMAG = "\033[95m";
    const string BCYN = "\033[96m";
    const string BWHT = "\033[97m";
}

// ================================================================
//  HELPERS
// ================================================================

static void enableAnsi() {
#ifdef _WIN32
    HANDLE h = GetStdHandle(STD_OUTPUT_HANDLE);
    DWORD mode = 0;
    GetConsoleMode(h, &mode);
    SetConsoleMode(h, mode | ENABLE_VIRTUAL_TERMINAL_PROCESSING);
#endif
}

static void cls()             { cout << "\033[2J\033[H"; }
static void sleep_ms(int ms)  { this_thread::sleep_for(chrono::milliseconds(ms)); }
static void flushIn()         { cin.clear(); cin.ignore(numeric_limits<streamsize>::max(), '\n'); }

static string timestamp() {
    time_t now = time(nullptr);
    char buf[20];
    strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M", localtime(&now));
    return string(buf);
}

static string centered(const string& s, int w) {
    int pad = max(0, (w - (int)s.size()) / 2);
    string r(pad, ' ');
    r += s;
    r += string(max(0, w - pad - (int)s.size()), ' ');
    return r;
}

static double readAmount(const string& lbl) {
    double v;
    while (true) {
        cout << C::DIM << "   " << lbl << " " << C::RST << C::BYLW << "$" << C::RST;
        if (cin >> v && v > 0.0) { flushIn(); return v; }
        cout << C::BRED << "   invalid — enter a positive number.\n" << C::RST;
        flushIn();
    }
}

static int readInt(const string& prompt, int lo, int hi) {
    int v;
    while (true) {
        cout << C::DIM << "   " << prompt << " " << C::RST;
        if (cin >> v && v >= lo && v <= hi) { flushIn(); return v; }
        cout << C::BRED << "   enter " << lo << "-" << hi << ".\n" << C::RST;
        flushIn();
    }
}

static string readPin(const string& prompt) {
    string s;
    cout << C::DIM << "   " << prompt << " " << C::RST;
    cin >> s; flushIn();
    return s;
}

static string readLine(const string& prompt) {
    string s;
    cout << C::DIM << "   " << prompt << " " << C::RST;
    getline(cin, s);
    return s;
}

static void anyKey() {
    cout << C::DIM << "\n   [ press enter ]" << C::RST;
    cin.get();
}

// ================================================================
//  BOX DRAWING  (pure ASCII - Windows safe)
// ================================================================
static const int W = 54;   // inner width of box

static void bTop(const string& ac = C::BCYN) {
    cout << "   " << ac << "+" << string(W, '-') << "+" << C::RST << "\n";
}
static void bBot(const string& ac = C::BCYN) {
    cout << "   " << ac << "+" << string(W, '-') << "+" << C::RST << "\n";
}
static void bSep(const string& ac = C::BCYN) {
    cout << "   " << ac << "|" << string(W, '-') << "|" << C::RST << "\n";
}
static void bMid(const string& ac = C::BCYN) {
    cout << "   " << ac << "|" << string(W, ' ') << "|" << C::RST << "\n";
}
static void bRow(const string& text,
                 const string& ac = C::BCYN,
                 const string& tc = C::BWHT) {
    cout << "   " << ac << "|" << C::RST
         << tc << centered(text, W) << C::RST
         << ac << "|" << C::RST << "\n";
}
static void bLeft(const string& text,
                  const string& ac = C::BCYN,
                  const string& tc = C::WHT) {
    string inner = "  " + text;
    if ((int)inner.size() < W - 1) inner += string(W - 1 - inner.size(), ' ');
    inner = inner.substr(0, W);
    cout << "   " << ac << "|" << C::RST << " "
         << tc << inner << C::RST
         << ac << "|" << C::RST << "\n";
}

// ================================================================
//  SPLASH  ASCII ART + LOADING BAR
// ================================================================
static void splash() {
    cls();
    cout << "\n\n";
    cout << C::BCYN << C::BOLD;
    cout << "          ___   ______ __  ___\n";
    cout << "         /   | /_  __//  |/  /\n";
    cout << "        / /| |  / /  / /|_/ / \n";
    cout << "       / ___ | / /  / /  / /  \n";
    cout << "      /_/  |_|/_/  /_/  /_/   \n";
    cout << C::RST;
    cout << C::CYN
         << "      A D V A N C E D   B A N K I N G   T E R M I N A L\n"
         << C::RST;
    cout << "\n";
    cout << "   " << C::DIM << "v2.4  |  secure session  |  " << timestamp() << C::RST << "\n\n";

    // Loading bar
    cout << "   " << C::DIM << "initializing  " << C::RST;
    cout << C::DIM << "[" << C::RST;
    for (int i = 0; i < 32; ++i) {
        sleep_ms(22);
        if      (i < 11) cout << C::BGRN  << "=" << C::RST << flush;
        else if (i < 22) cout << C::BYLW  << "=" << C::RST << flush;
        else             cout << C::BCYN  << "=" << C::RST << flush;
    }
    cout << C::DIM << "]  " << C::RST << C::BGRN << C::BOLD << "ready\n" << C::RST;
    sleep_ms(500);
}

// ================================================================
//  SCREEN HEADER
// ================================================================
static void header(const string& title, const string& ac = C::BCYN) {
    cls();
    cout << "\n";
    bTop(ac);
    bMid(ac);
    bRow("ATM  //  " + title, ac, ac + C::BOLD);
    bMid(ac);
    bSep(ac);
    cout << "\n";
}

// ================================================================
//  DATA
// ================================================================
struct Tx { string type, when; double amount, after; };

class Account {
    int    id_;
    string name_, pin_;
    double bal_;
    vector<Tx> hist_;
public:
    Account(int id, const string& n, const string& p, double b)
        : id_(id), name_(n), pin_(p), bal_(b) {}

    int           id()      const { return id_;   }
    string        name()    const { return name_; }
    double        balance() const { return bal_;  }
    const string& pin()     const { return pin_;  }
    bool checkPin(const string& p) const { return p == pin_; }
    const vector<Tx>& history()    const { return hist_; }

    void deposit(double a) { bal_ += a; hist_.push_back({"DEPOSIT",  timestamp(), a, bal_}); }
    bool withdraw(double a) {
        if (a > bal_) return false;
        bal_ -= a;
        hist_.push_back({"WITHDRAW", timestamp(), a, bal_});
        return true;
    }
};

class Bank {
    vector<Account> accs_;
    int nid_ = 1001;
public:
    Bank() {
        accs_.emplace_back(nid_++, "Shahab Ahmed", "1234", 5000.00);
        accs_.emplace_back(nid_++, "Sara Khan",    "4321", 3200.50);
        accs_.emplace_back(nid_++, "Ali Hassan",   "0000", 12500.75);
    }
    Account* find(int id) {
        for (auto& a : accs_) if (a.id() == id) return &a;
        return nullptr;
    }
    void add(const string& n, const string& p, double b) { accs_.emplace_back(nid_++, n, p, b); }
    bool remove(int id) {
        auto it = remove_if(accs_.begin(), accs_.end(), [id](const Account& a){ return a.id() == id; });
        if (it == accs_.end()) return false;
        accs_.erase(it, accs_.end());
        return true;
    }
    const vector<Account>& all() const { return accs_; }
    int count() const { return (int)accs_.size(); }
};

// ================================================================
//  ATM CONTROLLER
// ================================================================
class ATM {
    Bank& bank_;

    // ── account list ─────────────────────────────────────────
    void listAccounts(const string& ac = C::BCYN) {
        cout << "   " << ac << C::BOLD
             << left << setw(8)  << " ID"
             << setw(22) << "NAME"
             << right << setw(16) << "BALANCE"
             << C::RST << "\n";
        cout << "   " << ac << string(46, '-') << C::RST << "\n";
        for (auto& a : bank_.all()) {
            ostringstream b; b << "$" << fixed << setprecision(2) << a.balance();
            cout << "   " << C::DIM  << setw(8)  << left  << a.id()    << C::RST
                 << C::BWHT          << setw(22) << left  << a.name()  << C::RST
                 << C::BYLW          << setw(16) << right << b.str()   << C::RST << "\n";
        }
        cout << "\n";
    }

    // ── login ────────────────────────────────────────────────
    Account* doLogin() {
        header("SIGN IN");
        if (bank_.count() == 0) {
            cout << C::BRED << "   No accounts. Use Admin to create one.\n" << C::RST;
            anyKey(); return nullptr;
        }
        listAccounts();

        cout << C::DIM << "   Account ID: " << C::RST;
        int id; cin >> id; flushIn();
        Account* acc = bank_.find(id);
        if (!acc) {
            cout << C::BRED << "\n   Account not found.\n" << C::RST;
            anyKey(); return nullptr;
        }

        cout << "\n";
        for (int t = 1; t <= 3; ++t) {
            string p = readPin("PIN (" + to_string(t) + "/3):");

            // animated dots
            cout << "   ";
            for (int i = 0; i < (int)p.size() && i < 4; ++i) {
                sleep_ms(80);
                cout << C::BCYN << "* " << C::RST << flush;
            }
            cout << "\n";

            if (acc->checkPin(p)) {
                cout << "\n";
                bTop(C::BGRN);
                bRow("ACCESS GRANTED", C::BGRN, C::BGRN + C::BOLD);
                bRow("Welcome, " + acc->name(), C::BGRN, C::BWHT);
                bBot(C::BGRN);
                sleep_ms(900);
                return acc;
            }
            cout << C::BRED << "   Incorrect. " << (3 - t) << " attempt(s) left.\n\n" << C::RST;
        }

        cout << "\n";
        bTop(C::BRED);
        bRow("CARD BLOCKED", C::BRED, C::BRED + C::BOLD);
        bRow("Contact your bank for assistance.", C::BRED, C::WHT);
        bBot(C::BRED);
        anyKey(); return nullptr;
    }

    // ── balance ──────────────────────────────────────────────
    void showBalance(Account* acc) {
        header("BALANCE  //  " + acc->name(), C::BCYN);
        cout << "\n";
        bTop(C::BCYN);
        bMid(C::BCYN);
        ostringstream s; s << "$" << fixed << setprecision(2) << acc->balance();
        bRow(s.str(), C::BCYN, C::BYLW + C::BOLD);
        bRow("available balance", C::BCYN, C::DIM);
        bMid(C::BCYN);
        bBot(C::BCYN);
        cout << "\n"; anyKey();
    }

    // ── deposit ──────────────────────────────────────────────
    void doDeposit(Account* acc) {
        header("DEPOSIT  //  " + acc->name(), C::BGRN);
        cout << C::DIM << "   Current balance: " << C::RST
             << C::BYLW << "$" << fixed << setprecision(2) << acc->balance() << C::RST << "\n\n";
        double amt = readAmount("Amount to deposit:");
        acc->deposit(amt);
        cout << "\n";
        bTop(C::BGRN);
        ostringstream s; s << "+ $" << fixed << setprecision(2) << amt << "  deposited";
        bRow(s.str(), C::BGRN, C::BGRN + C::BOLD);
        ostringstream b; b << "New balance: $" << fixed << setprecision(2) << acc->balance();
        bRow(b.str(), C::BGRN, C::BWHT);
        bBot(C::BGRN);
        cout << "\n"; anyKey();
    }

    // ── withdraw ─────────────────────────────────────────────
    void doWithdraw(Account* acc) {
        header("WITHDRAW  //  " + acc->name(), C::BYLW);
        cout << C::DIM << "   Current balance: " << C::RST
             << C::BYLW << "$" << fixed << setprecision(2) << acc->balance() << C::RST << "\n\n";
        double amt = readAmount("Amount to withdraw:");

        if (!acc->withdraw(amt)) {
            cout << "\n";
            bTop(C::BRED);
            bRow("INSUFFICIENT FUNDS", C::BRED, C::BRED + C::BOLD);
            ostringstream s; s << "Available: $" << fixed << setprecision(2) << acc->balance();
            bRow(s.str(), C::BRED, C::WHT);
            bBot(C::BRED);
        } else {
            cout << "\n";
            bTop(C::BYLW);
            ostringstream s; s << "- $" << fixed << setprecision(2) << amt << "  withdrawn";
            bRow(s.str(), C::BYLW, C::BYLW + C::BOLD);
            ostringstream b; b << "New balance: $" << fixed << setprecision(2) << acc->balance();
            bRow(b.str(), C::BYLW, C::BWHT);
            bBot(C::BYLW);
        }
        cout << "\n"; anyKey();
    }

    // ── history ──────────────────────────────────────────────
    void showHistory(Account* acc) {
        header("HISTORY  //  " + acc->name(), C::BMAG);
        const auto& h = acc->history();
        if (h.empty()) {
            bTop(C::BMAG); bRow("No transactions on record.", C::BMAG, C::DIM); bBot(C::BMAG);
            cout << "\n"; anyKey(); return;
        }
        cout << "   " << C::BMAG << C::BOLD
             << left << setw(10) << "TYPE"
             << right << setw(12) << "AMOUNT"
             << setw(14) << "BALANCE"
             << "  " << left << "TIME"
             << C::RST << "\n";
        cout << "   " << C::BMAG << string(52, '-') << C::RST << "\n";
        int start = max(0, (int)h.size() - 15);
        for (int i = start; i < (int)h.size(); ++i) {
            const auto& t = h[i];
            string tc   = (t.type == "DEPOSIT") ? C::BGRN : C::BRED;
            string sign = (t.type == "DEPOSIT") ? "+" : "-";
            ostringstream amt, bal;
            amt << sign << "$" << fixed << setprecision(2) << t.amount;
            bal << "$"  << fixed << setprecision(2) << t.after;
            cout << "   " << tc    << left  << setw(10) << t.type   << C::RST
                          << tc    << right << setw(12) << amt.str() << C::RST
                          << C::BYLW        << setw(14) << bal.str() << C::RST
                 << "  "  << C::DIM << left << t.when               << C::RST << "\n";
        }
        cout << "\n"; anyKey();
    }

    // ── dashboard ────────────────────────────────────────────
    void dashboard(Account* acc) {
        while (true) {
            header("DASHBOARD  //  " + acc->name());
            cout << "   " << C::DIM << "balance  " << C::RST
                 << C::BYLW << C::BOLD << "$" << fixed << setprecision(2)
                 << acc->balance() << C::RST << "\n\n";

            bTop();
            bRow("WHAT WOULD YOU LIKE TO DO?", C::BCYN, C::DIM);
            bSep();
            bLeft("1   check balance",        C::BCYN, C::BWHT);
            bLeft("2   deposit",              C::BCYN, C::BWHT);
            bLeft("3   withdraw",             C::BCYN, C::BWHT);
            bLeft("4   transaction history",  C::BCYN, C::BWHT);
            bLeft("5   logout",               C::BCYN, C::DIM);
            bBot();

            switch (readInt("choice (1-5):", 1, 5)) {
                case 1: showBalance(acc);  break;
                case 2: doDeposit(acc);    break;
                case 3: doWithdraw(acc);   break;
                case 4: showHistory(acc);  break;
                case 5:
                    cout << C::DIM << "\n   Session ended.\n" << C::RST;
                    sleep_ms(600); return;
            }
        }
    }

    // ── admin ────────────────────────────────────────────────
    void adminPanel() {
        header("ADMIN ACCESS", C::BMAG);
        cout << C::DIM << "   Demo admin PIN: 9999\n\n" << C::RST;
        if (readPin("Admin PIN:") != "9999") {
            cout << "\n";
            bTop(C::BRED); bRow("ACCESS DENIED", C::BRED, C::BRED + C::BOLD); bBot(C::BRED);
            anyKey(); return;
        }

        while (true) {
            header("ADMIN PANEL", C::BMAG);
            listAccounts(C::BMAG);

            bTop(C::BMAG);
            bRow("ADMIN OPERATIONS", C::BMAG, C::DIM);
            bSep(C::BMAG);
            bLeft("1   add account",    C::BMAG, C::BWHT);
            bLeft("2   delete account", C::BMAG, C::BWHT);
            bLeft("3   back",           C::BMAG, C::DIM);
            bBot(C::BMAG);

            int ch = readInt("choice (1-3):", 1, 3);
            if (ch == 3) return;

            if (ch == 1) {
                header("NEW ACCOUNT", C::BGRN);
                string name = readLine("Full name:");
                if (name.empty()) { cout << C::BRED << "   Name required.\n" << C::RST; anyKey(); continue; }
                string pin = readPin("PIN (4 digits):");
                if (pin.size() != 4 || !all_of(pin.begin(), pin.end(), ::isdigit)) {
                    cout << C::BRED << "   PIN must be 4 digits.\n" << C::RST; anyKey(); continue;
                }
                double bal = readAmount("Initial deposit:");
                bank_.add(name, pin, bal);
                cout << "\n";
                bTop(C::BGRN);
                bRow("Account created for " + name, C::BGRN, C::BGRN + C::BOLD);
                bBot(C::BGRN);
                anyKey();
            }

            if (ch == 2) {
                header("DELETE ACCOUNT", C::BRED);
                if (bank_.count() == 0) { cout << C::DIM << "   No accounts.\n" << C::RST; anyKey(); continue; }
                listAccounts(C::BRED);
                cout << C::DIM << "   Account ID to delete: " << C::RST;
                int id; cin >> id; flushIn();
                Account* t = bank_.find(id);
                if (!t) { cout << C::BRED << "   Not found.\n" << C::RST; anyKey(); continue; }
                cout << C::BYLW << "   Delete \"" << t->name() << "\"? (y/n): " << C::RST;
                char c; cin >> c; flushIn();
                if (c == 'y' || c == 'Y') {
                    bank_.remove(id);
                    cout << C::BGRN << "   Deleted.\n" << C::RST;
                } else { cout << C::DIM << "   Cancelled.\n" << C::RST; }
                anyKey();
            }
        }
    }

public:
    ATM(Bank& b) : bank_(b) {}

    void run() {
        splash();
        while (true) {
            header("MAIN MENU");
            bTop(); bRow("SELECT AN OPTION", C::BCYN, C::DIM); bSep();
            bLeft("1   sign in",  C::BCYN, C::BWHT);
            bLeft("2   admin",    C::BCYN, C::BWHT);
            bLeft("3   quit",     C::BCYN, C::DIM);
            bBot();

            switch (readInt("choice (1-3):", 1, 3)) {
                case 1: { Account* a = doLogin(); if (a) dashboard(a); break; }
                case 2: adminPanel(); break;
                case 3:
                    cls(); cout << "\n";
                    bTop(C::BCYN); bMid(C::BCYN);
                    bRow("Thank you for banking with us.", C::BCYN, C::BCYN + C::BOLD);
                    bRow("Goodbye.", C::BCYN, C::DIM);
                    bMid(C::BCYN); bBot(C::BCYN);
                    cout << "\n";
                    return;
            }
        }
    }
};

// ================================================================
//  MAIN
// ================================================================
int main() {
    enableAnsi();
    Bank bank;
    ATM  atm(bank);
    atm.run();
    return 0;
}
