// ----------- Pragma Optimizations (Safe) ------------
#pragma GCC optimize("O3,unroll-loops")
#pragma GCC target("avx2,bmi,bmi2,lzcnt,popcnt")

#include <bits/stdc++.h>
#include <ext/pb_ds/assoc_container.hpp>
#include <ext/pb_ds/tree_policy.hpp>
using namespace std;
using namespace __gnu_pbds;

// ----------- Fast Typing ------------
#define int long long
#define pb push_back
#define ff first
#define ss second
#define endl '\n'
#define all(x) (x).begin(), (x).end()
#define rall(x) (x).rbegin(), (x).rend()
#define vi vector<int>
#define pii pair<int, int>
#define vpii vector<pii>
#define yes cout << "YES\n"
#define no cout << "NO\n"

// ----------- Ordered Set (policy-based) ------------
// 
// Provides: 
//  - order_of_key(k): Number of elements strictly less than k
//  - find_by_order(k): Iterator to k-th element (0-based)
//
template <typename T>
using ordered_set = tree<
    T,
    null_type,
    less<T>,
    rb_tree_tag,
    tree_order_statistics_node_update
>;

// ----------- Debug Tools ------------
#ifndef ONLINE_JUDGE
    #define debug(x) cerr << #x << " = "; _print(x); cerr << endl;
#else
    #define debug(x)
#endif

void _print(int x) { cerr << x; }
void _print(string x) { cerr << x; }
void _print(char x) { cerr << x; }
void _print(bool x) { cerr << (x ? "true" : "false"); }

template<typename T, typename V> void _print(pair<T, V>);
template<typename T> void _print(vector<T>);
template<typename T> void _print(set<T>);
template<typename T, typename V> void _print(map<T, V>);

template<typename T, typename V>
void _print(pair<T, V> p) { cerr << "{"; _print(p.ff); cerr << ", "; _print(p.ss); cerr << "}"; }

template<typename T>
void _print(vector<T> v) {
    cerr << "[ ";
    for (T i : v) _print(i), cerr << " ";
    cerr << "]";
}

template<typename T>
void _print(set<T> v) {
    cerr << "{ ";
    for (T i : v) _print(i), cerr << " ";
    cerr << "}";
}

template<typename T, typename V>
void _print(map<T, V> v) {
    cerr << "{ ";
    for (auto i : v) _print(i), cerr << " ";
    cerr << "}";
}

// ----------- Random Generator ------------
mt19937 rng(chrono::steady_clock::now().time_since_epoch().count());
int randInt(int l, int r) {
    return uniform_int_distribution<int>(l, r)(rng);
}

// ----------- Constants ------------
const int MOD = 1e9 + 7;
const int INF = 1e18;
const int N = 2e5 + 5;

// ----------- Useful Functions ------------
int gcd(int a, int b) { return b == 0 ? a : gcd(b, a % b); }
int lcm(int a, int b) { return (a / gcd(a, b)) * b; }

// ----------- Main Solve Function ------------
void solve() {
    // Your logic goes here
}

// ----------- Main Function ------------
int32_t main() {
    ios::sync_with_stdio(false);
    cin.tie(0);
    cout.tie(0);

#ifndef ONLINE_JUDGE
    freopen("input.txt", "r", stdin);
    freopen("output.txt", "w", stdout);
    freopen("debug.txt", "w", stderr);
#endif

    int t = 1;
    // cin >> t;
    while (t--) solve();

    return 0;
}
